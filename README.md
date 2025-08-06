# Realtime Quiz

A real-time 4 player quiz game where two teams of two compete based on correctness and speed of answers.

## 🧠 Features
- Real-time 2v2 quiz battles
- Automatic matchmaking by subject
- 60-second timed quiz
- Global & location-based leaderboards
- Game results persisted in SQLite

---

## 🚀 How It Works

### Quiz Flow
1. A user inputs a subject to play **["maths", "science", "general_knowledge"]**.
2. System matches them with a teammate and finds an opponent team based on subject.
3. A 60-second quiz starts via WebSocket connection.
4. Players answer questions in real time.
5. Score is calculated using:
   - +10 for correct answer
   - +bonus (up to 10) based on time
6. Winning team is declared.
7. Results are saved to DB.
8. Global & country-based leaderboards are shown at the end of each game.

---

## 🏗️ Tech Stack Overview

- **FastAPI** – REST APIs and WebSocket endpoints
- **Redis** – Matchmaking queue, game state, and scores
- **SQLite** – Storing player data and match results
- **WebSocket** – Real-time game logic and updates

---

## 🖥️ API Endpoints

### `POST /join-match`
- Create unique user based on username
- Adds user to matchmaking queue.
- Automatically starts a game when 4 users are queued.

### `GET /leaderboard/`
- Returns top 10 global players based on total score.

### `GET /leaderboard/{country}/`
- Returns top 10 players by country. (If country is known)

### `WebSocket /ws/{game_id}/{user_id}`
- Manages real-time game flow (questions, answers, scoring, result).
### `WebSocket /ws/answer/{game_id}/{user_id}`
- Manages real-time questions answer.
User need to provide Json with {"question_id":1, "answer":7}

---

## 💾 Database Models

- **Player**: `id`, `user_name`, `country`
- **GameResult**: `id`, `subject`, `team1_score`, `team2_score`, `winner`, `created_at`
- **PlayerScore**: `id`, `game_id`, `player_id`, `score`

---

## 🧪 Setup & Run Locally

### 1. Clone the repo

```
    git clone git@github.com:rishiqwerty/multiplayer-quiz.git
    cd multiplayer-quiz
```

### 2. Create env and Install dependency via Poetry
```
    direnv allow # can use venv also
    poetry install
```
### 3. Run redis server and fast api server
```
    redis-server
    uvicorn app.main:app --host 0.0.0.0 --port 8009
```

## Assignment Q&A

### Q1: How would you handle real-time communication and synchronization between players?

- I use WebSockets to maintain realtime communication and sync. Each player connects via `ws://localhost:8009/ws/{game_id}/{user_id}`, and the server broadcasts quiz questions and scores to all players in real time. Game state and answers are tracked in Redis for synchronization.

### Q2: What strategy would you use for scaling the matchmaking service under heavy load?

- Redis lists is used for matchmaking queues by subject. Under heavy load, I would:
- Partition queues by subject.
- Use distributed Redis or Redis Cluster.
- Run matchmaking logic in background worker with batching to reduce load on Redis.

### Q3: How would you ensure the scoring service meets the performance SLA (p95 < 200ms)?

- Scoring is done in-memory via Redis to maintain low-latency requirements. Redis stores scores with expiry. Final scores are asynchronously persisted to SQLite.

### Q4: If the quiz involved dynamic or user-generated questions, how would that impact your design?
- Would add a question ingestion service with validation and moderation.
- Store questions in database.
- Cache recently used or frequently used question.
- During gametime i will preload questions in redis before starting the game.

### Quiz Example
```
# Websocket for questions
➜  ~ websocat ws://localhost:8009/ws/0d39eb4e-f658-44ee-9a2c-3624b0d57676/7
{"team1":"9,7","team2":"8,11","status":"started"}
{"type":"question","question_id":1,"question":"What is 5 + 7?","options":["10","12","14"]}
{"type":"score_update","scores":{"9":"0","7":"0","8":"0","11":"0"}}
{"type":"question","question_id":2,"question":"Square root of 49?","options":["6","7","8"]}

# Websocket for answering questions
➜  ~ websocat ws://localhost:8009/ws/answer/5eabc28f-c73f-4257-bbb5-1ee99e9c57f6/8
{"question_id": 2, "answer": "7"}
```
