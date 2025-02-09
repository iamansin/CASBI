import asyncio
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
import json
from ..logger import LOGGER
from ..prompts import MEMORY_PROMPT
from langchain_core.prompts import PromptTemplate
from datetime import datetime, timedelta

# Redis & MongoDB Connection
REDIS_URL = "redis://localhost:6379"
MONGO_URL = "mongodb://127.0.0.1:27017"

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["memory_Store"]
collection = db["user_memory"]

# Expiry time for Redis cache (10 minutes)
REDIS_EXPIRY = 600  # 10 minutes

async def retrieve_memory(phone_number: str) -> list[dict]:
    """
    Retrieves the conversation memory of a user.
    First, it checks Redis for cached memory. If not found, it fetches from MongoDB,
    updates Redis, and returns the memory as a list of strings.
    """
    redis_key = f"user_long_term_memory:{phone_number}"

    # Check Redis first
    memory_json = await redis_client.get(redis_key)
    if memory_json:
        mem = json.loads(memory_json)
        if isinstance(mem, list):
            return mem # Return cached memory
        return [mem]

    # If not in Redis, retrieve from MongoDB
    user_data = await collection.find_one({"phone_number": phone_number}, {"_id": 0, "long_term_memory": 1})

    if user_data and "long_term_memory" in user_data:
        memory = user_data["long_term_memory"]
        # Store in Redis with expiry
        await redis_client.setex(redis_key, REDIS_EXPIRY, json.dumps(memory))
        return memory

    return [{"long_term_memory" : "No previous memory, New user"}]  


# Dictionary to track active timers

async def store_memory(phone_number: str, new_messages: list[dict], timers: dict):
    """
    Stores short-term memory in Redis for fast retrieval.
    Resets the timer on new messages. Transfers long-term memory to MongoDB after 10 min of inactivity.
    """
    redis_key = f"user_memory:{phone_number}"
    last_message_key = f"last_message:{phone_number}"

    # Retrieve existing short-term memory from Redis
    existing_memory_json = await redis_client.get(redis_key)
    existing_memory = json.loads(existing_memory_json) if existing_memory_json else {"long_term_history":[] ,"short_term_memory": []}
    

    # Process new messages
    for msg in new_messages:
        if "short_term_memory" in msg:
            existing_memory["short_term_memory"].extend(msg["short_term_memory"])
    
    now_timestamp = datetime.utcnow().timestamp()
    async with redis_client.pipeline() as pipe:
        pipe.setex(redis_key, REDIS_EXPIRY, json.dumps(existing_memory))
        pipe.set(last_message_key, now_timestamp, ex=REDIS_EXPIRY)
        await pipe.execute()

    # Reset and start a new timer
    if phone_number in timers:
        timers[phone_number].cancel()
    
    timers[phone_number] = asyncio.create_task(schedule_mongo_transfer(phone_number))

async def schedule_mongo_transfer(phone_number: str):
    """
    Waits for 10 minutes of inactivity before transferring long-term memory from Redis to MongoDB.
    """
    await asyncio.sleep(REDIS_EXPIRY)  # 10 minutes delay

    redis_key = f"user_memory:{phone_number}"
    last_message_key = f"last_message:{phone_number}"

    # Retrieve last message timestamp
    last_timestamp = await redis_client.get(last_message_key)
    if last_timestamp and (datetime.utcnow().timestamp() - float(last_timestamp)) < REDIS_EXPIRY:
        return  

    # Retrieve memory from Redis
    existing_memory_json = await redis_client.get(redis_key)
    if not existing_memory_json:
        return  # Nothing to transfer

    existing_memory = json.loads(existing_memory_json)

    # Extract long-term history only
    short_term_memory = existing_memory.get("short_term_memory", [])
    to_be_saved_memory = await extract_long_term_memory(short_term_memory)
    if to_be_saved_memory:
        await transfer_long_term_to_mongo(phone_number, to_be_saved_memory)

    # Remove from Redis
    async with redis_client.pipeline() as pipe:
        pipe.delete(redis_key)
        pipe.delete(last_message_key)
        await pipe.execute()

async def transfer_long_term_to_mongo(phone_number: str,to_be_saved_memory: list[str]):
    """
    Transfers long-term memory to MongoDB.
    """
    if not to_be_saved_memory:
        return

    # Update or insert memory into MongoDB
    await collection.update_one(
        {"phone_number": phone_number},
        {"$push": {"long_term_history": {"$each": to_be_saved_memory}}},
        upsert=True
    )

async def extract_long_term_memory(short_term_memory: list[str], llm) -> list[str]:
    """
    Extracts long-term memory from short-term memory.
    """
    temp = PromptTemplate(template = MEMORY_PROMPT)
    message = temp.format(session_conversation = short_term_memory)
    try:
        response = await llm.ainvoke(message)
        return [response.content] if response.content else False
        
    except Exception as e:
        LOGGER.error(f"Failed to extract long-term memory: {str(e)}")
        return False
        
