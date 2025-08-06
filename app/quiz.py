questions_bank = {
    "queue:maths": [
        {
            "id": 1,
            "question": "What is 5 + 7?",
            "options": ["10", "12", "14"],
            "answer": "12",
        },
        {
            "id": 2,
            "question": "Square root of 49?",
            "options": ["6", "7", "8"],
            "answer": "7",
        },
        {
            "id": 3,
            "question": "What is 20% of 200?",
            "options": ["25", "30", "40"],
            "answer": "40",
        },
    ],
    "queue:general_knowledge": [
        {
            "id": 1,
            "question": "What is the capital of France?",
            "options": ["Berlin", "Madrid", "Paris"],
            "answer": "Paris",
        },
        {
            "id": 2,
            "question": "Who wrote 'Hamlet'?",
            "options": ["Shakespeare", "Hemingway", "Tolkien"],
            "answer": "Shakespeare",
        },
        {
            "id": 3,
            "question": "What is the largest planet in our solar system?",
            "options": ["Earth", "Jupiter", "Saturn"],
            "answer": "Jupiter",
        },
    ],
    "queue:science": [
        {
            "id": 1,
            "question": "What is H2O commonly known as?",
            "options": ["Oxygen", "Water", "Hydrogen"],
            "answer": "Water",
        },
        {
            "id": 2,
            "question": "What is the chemical symbol for Gold?",
            "options": ["Au", "Ag", "Pb"],
            "answer": "Au",
        },
        {
            "id": 3,
            "question": "What is the speed of light?",
            "options": ["300,000 km/s", "150,000 km/s", "450,000 km/s"],
            "answer": "300,000 km/s",
        },
    ],
}


def get_questions(subject: str, count: int = 5):
    # print(subject)
    return questions_bank[subject][:count]


# # QUEUEING requests to a base server
# # - Base server can handle 10 requests persecond, we have requests in queue
# #  We can have a worker that processes these requests we can increase the number of workers if needed
# # RATE LIMITING
# # CACHING
# # Drop low-priority requests or use request deduplication (batching)
# import asyncio
# import uuid
# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# import httpx

# app = FastAPI()

# MAX_QUEUE_SIZE = 100  # Maximum number of requests in the queue
# # Shared queue to hold incoming requests
# request_queue = asyncio.Queue()

# # Dictionary to map request_id -> Future (so we can return response)
# pending_futures = {}

# # Base server URL
# BASE_SERVER_URL = "http://localhost:8001"

# client = httpx.AsyncClient()

# # Worker that pulls from queue and talks to base server
# async def worker():
#     while True:
#         request_id, endpoint = await request_queue.get()
#         future = pending_futures[request_id]

#         try:
#             resp = await client.get(f"{BASE_SERVER_URL}{endpoint}")
#             future.set_result(resp.json())
#         except Exception as e:
#             future.set_result({"error": str(e)})

#         request_queue.task_done()

# # Start the worker in the background
# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(worker())

# @app.get("/proxy/{path:path}")
# async def proxy_handler(path: str, request: Request):
#     # Create a unique ID and future
#     if request_queue.qsize() >= MAX_QUEUE_SIZE:
#         return JSONResponse({"error": "Too many requests"}, status_code=429)

#     request_id = str(uuid.uuid4())
#     future = asyncio.get_event_loop().create_future()
#     pending_futures[request_id] = future

#     # Add to queue
#     await request_queue.put((request_id, f"/{path}"))

#     # Wait for result (from worker)
#     result = await future

#     # Clean up
#     del pending_futures[request_id]
#     return JSONResponse(result)
