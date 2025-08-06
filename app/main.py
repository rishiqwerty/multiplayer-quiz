import asyncio
import json
import time
from typing import List, Optional
import uuid
from app.quiz import get_questions
import httpx
from fastapi import FastAPI
import redis.asyncio as redis
from sqlalchemy import func, desc

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
from pydantic import BaseModel
from app.websocket import router as websocket_router
from app.models import Player, PlayerScore, GameResult, SessionLocal
from app.leader_board import get_global_leaderboard

MATCH_BATCH_SIZE = 4
QUESTIONS_AVAILABLE = ["maths", "science", "general_knowledge"]


class MatchRequest(BaseModel):
    user_name: str
    subject: str
    country: Optional[str] = ""


app = FastAPI()
app.include_router(websocket_router)


@app.on_event("startup")
async def start_matchmaking():
    asyncio.create_task(matchmaking())


queue = {}


@app.get("/health")
async def health_check():
    return {"Ping": "Pong"}


# Matchmaking
@app.post("/join-match")
async def join_match(data: MatchRequest):
    """
    Join match queue, new user will be created if not exists
    Choose from these subjects: maths, science, general_knowledge
    """
    username = data.user_name
    subject = data.subject
    if subject not in QUESTIONS_AVAILABLE:
        return {
            "error": "Invalid subject. Choose from: maths, science, general_knowledge (CASE_SENSITIVE)"
        }
    queue_key = f"queue:{subject}"
    country = data.country

    db = SessionLocal()
    player = db.query(Player).filter_by(user_name=username).first()
    if not player:
        player = Player(user_name=username, country=country.lower())
        db.add(player)
        db.commit()
    user_id = player.id
    db.close()

    await r.rpush(queue_key, user_id)
    return {"message": f"{user_id} added to matchmaking queue for {subject}"}


async def matchmaking():
    while True:
        subjects = await r.keys("queue:*")
        for subject in subjects:
            await batch_match_subject(subject)


async def batch_match_subject(subject: str):
    """
    Match users for a specific subject
    If there are 4 users in the queue, create a game
    and store it in Redis
    """
    queue_key = f"{subject}"
    users = await r.lrange(queue_key, 0, MATCH_BATCH_SIZE - 1)
    print(f"Matching users for subject {queue_key}: {users}")

    if len(users) < MATCH_BATCH_SIZE:
        return
    print("Length of users:", subject, len(users))

    await r.ltrim(queue_key, MATCH_BATCH_SIZE, -1)

    team1 = users[0:2]
    team2 = users[2:4]
    game_id = str(uuid.uuid4())
    game_key = f"game:{game_id}"
    questions = get_questions(subject)

    await r.hset(
        game_key,
        mapping={
            "subject": subject,
            "team1": ",".join(team1),
            "team2": ",".join(team2),
            "status": "waiting",
            "questions": json.dumps(questions),
        },
    )
    print(f"Game created with ID {game_key} for subject {subject}")
    await r.expire(game_key, 300)

    print(f"Matched game {game_id}: {team1} vs {team2}")


## Results Endpoints
@app.get("/leaderboard/")
async def leaderboard():
    leaderboard = await get_global_leaderboard()
    return {"leaderboard": leaderboard}


@app.get("/leaderboard/{country}")
async def location_leaderboard(country: str):
    """Leaderboard by country"""
    leaderboard = await get_global_leaderboard(country=country)
    return {"country": country.upper(), "leaderboard": leaderboard}


@app.get("/games-results/{user_id}")
async def get_games(user_id: str):
    """Get players last 10 games results"""
    db = SessionLocal()
    player = db.query(Player).filter_by(id=user_id).first()
    if not player:
        return {"error": "Player not found"}
    games = (
        db.query(GameResult)
        .join(PlayerScore, PlayerScore.game_id == GameResult.game_id)
        .filter(PlayerScore.player_id == player.id)
        .order_by(desc("id"))
        .limit(10)
        .all()
    )
    db.close()
    return {"games": games}
