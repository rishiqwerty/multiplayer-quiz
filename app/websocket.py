from fastapi import WebSocket, APIRouter
import redis.asyncio as redis
import asyncio, json, time
from app.models import GameResult, PlayerScore, SessionLocal
from app.leader_board import get_global_leaderboard


async def save_result_to_db(
    game_id, game_data, team1_score, team2_score, winner, scores
):
    """
    Save game result to database
    """
    try:
        db = SessionLocal()
        result = GameResult(
            game_id=game_id,
            team1=game_data["team1"],
            team2=game_data["team2"],
            team1_score=team1_score,
            team2_score=team2_score,
            winner=winner,
            final_scores=scores,
        )
        db.add(result)
        db.commit()
        for player_id, score in scores.items():
            player_score = PlayerScore(
                game_id=game_id, player_id=player_id, score=score
            )
        db.add(player_score)
        db.commit()
    except Exception as e:
        print(f"Error saving game result to DB: {e}")
    finally:
        db.close()


router = APIRouter()
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

connections = {}


@router.websocket("/ws/{game_id}/{user_id}")
async def quiz_websocket(websocket: WebSocket, game_id: str, user_id: str):
    await websocket.accept()

    if game_id not in connections:
        connections[game_id] = []
    connections[game_id].append(websocket)

    game_key = f"game:{game_id}"
    game_data = await r.hgetall(game_key)
    score_key = f"{game_key}:scores"

    if not game_data:
        await websocket.send_json({"error": "Invalid game"})
        await websocket.close()
        return

    questions = json.loads(game_data["questions"])

    all_users = game_data["team1"].split(",") + game_data["team2"].split(",")

    pipe = r.pipeline()
    for uid in all_users:
        pipe.hset(score_key, uid, 0)
    await pipe.execute()
    await broadcast(
        game_id,
        {"team1": game_data["team1"], "team2": game_data["team2"], "status": "started"},
    )
    # Send questions one by one with delay
    for q in questions:
        start_time = time.time()
        await broadcast(
            game_id,
            {
                "type": "question",
                "question_id": q["id"],
                "question": q["question"],
                "options": q["options"],
            },
        )

        try:
            # Wait 20 seconds for answers
            answers = await collect_answers(game_id, q["id"], timeout=20)
            print("******", answers)
        except asyncio.TimeoutError:
            answers = {}

        # Score answers
        for uid, ans_data in answers.items():
            if isinstance(ans_data, dict):
                answer = ans_data.get("answer")
                timestamp = ans_data.get("timestamp")
            else:
                continue
            if answer == q["answer"]:
                bonus = max(10 - int(timestamp - start_time), 0)
                await r.hincrby(score_key, uid, 10 + bonus)

        await broadcast(
            game_id, {"type": "score_update", "scores": await r.hgetall(score_key)}
        )

    # Final results
    final_scores = await r.hgetall(score_key)
    team1_score = sum(
        int(final_scores.get(uid, 0)) for uid in game_data["team1"].split(",")
    )
    team2_score = sum(
        int(final_scores.get(uid, 0)) for uid in game_data["team2"].split(",")
    )
    if team1_score > team2_score:
        winner = "team1"
    elif team1_score < team2_score:
        winner = "team2"
    else:
        winner = "draw"
    await broadcast(
        game_id,
        {
            "type": "game_over",
            "winner": winner,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "final_scores": final_scores,
        },
    )
    await save_result_to_db(
        game_id, game_data, team1_score, team2_score, winner, final_scores
    )
    global_leaderboard = await get_global_leaderboard()
    local_leaderboard = await get_global_leaderboard(user_id=user_id)
    await broadcast(
        game_id,
        {
            "type": "leaderboard",
            "global": global_leaderboard,
            "local": local_leaderboard,
        },
    )

    # Clean up redis data
    await r.delete(game_key)
    await r.delete(score_key)

    del connections[game_id]


async def broadcast(game_id, message):
    for ws in connections.get(game_id, []):
        await ws.send_json(message)


answer_buffer = {}


async def collect_answers(game_id, question_id, timeout=45):
    global answer_buffer
    if game_id not in answer_buffer:
        answer_buffer[game_id] = {}
    answer_buffer[game_id][question_id] = {}

    await asyncio.sleep(timeout)

    return answer_buffer[game_id][question_id]


@router.websocket("/ws/answer/{game_id}/{user_id}")
async def receive_answer(websocket: WebSocket, game_id: str, user_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        answer = data.get("answer")
        question_id = data.get("question_id")

        if answer and game_id in answer_buffer and question_id:
            answer_buffer[game_id][question_id][user_id] = {
                "answer": answer,
                "timestamp": time.time(),
            }
