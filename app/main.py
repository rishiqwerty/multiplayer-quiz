
import asyncio
import json
import time
from typing import List
import uuid
import httpx
from fastapi import FastAPI, Request
import redis.asyncio as redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
from pydantic import BaseModel
from app.websocket import router as websocket_router

MATCH_BATCH_SIZE = 4

class MatchRequest(BaseModel):
    user_id: str
    subject: str

app = FastAPI()
app.include_router(websocket_router)

@app.on_event("startup")
async def start_matchmaking():
    asyncio.create_task(matchmaking())
queue = {}

@app.get("/health")
async def health_check():
    return {"Ping": "Pong"}

@app.post("/join-match")
async def join_match(data: MatchRequest):
    user_id = data.user_id
    subject = data.subject
    queue_key = f"queue:{subject}"
    
    await r.rpush(queue_key, user_id)
    queues = await get_subjects_with_queue()
    print("Current queues:", queues)
    return {"message": f"{user_id} added to matchmaking queue for {subject}"}

async def matchmaking():
    while True:
        subjects = await r.keys("queue:*")
        await asyncio.sleep(5)  # Check every 5 seconds
        for subject in subjects:
            await batch_match_subject(subject)

async def get_subjects_with_queue() -> List[str]:
    keys = await r.keys("queue:*")
    return [key.split(":")[1] for key in keys]

async def batch_match_subject(subject: str):
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


    await r.hset(game_key, mapping={
        "subject": subject,
        "team1": ",".join(team1),
        "team2": ",".join(team2),
        "status": "waiting",
    })
    print(f"Game created with ID {game_key} for subject {subject}")
    await r.expire(game_key, 300)

    print(f"Matched game {game_id}: {team1} vs {team2}")

    
