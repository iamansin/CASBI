import asyncio
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
import json
from logger import LOGGER
from prompts import MEMORY_PROMPT
from langchain_core.prompts import PromptTemplate
from datetime import datetime, timedelta
from langchain.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from .agent_state import Memory_Structured_Output
from config import GROQ_API_KEY

LLM = ChatGroq(api_key = GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.0)

# Redis & MongoDB Connection
REDIS_URL = "redis://localhost:6379"
MONGO_URL = "mongodb://127.0.0.1:27017"

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["memory_Store"]
collection = db["user_memory"]

# Expiry time for Redis cache (10 minutes)
REDIS_EXPIRY = 120  # 10 minutes

async def retrieve_memory(phone_number: str) -> dict:
    """
    Retrieves the conversation memory of a user.
    First, it checks Redis for cached memory. If not found, it fetches from MongoDB,
    updates Redis, and returns the memory as a list of strings.
    """
    LOGGER.info(f"Starting memory retrieval for phone number: {phone_number}")
    redis_key = f"user_long_term_memory:{phone_number}"
    
    # Check Redis first
    LOGGER.info(f"Checking Redis for key: {redis_key}")
    memory_json = await redis_client.get(redis_key)
    
    if memory_json:
        LOGGER.info(f"Found cached memory in Redis for phone number: {phone_number}")
        try:
            mem = json.loads(memory_json)
            LOGGER.info(f"Successfully parsed Redis memory data for phone number: {phone_number}")
            LOGGER.info(f"The memory is {mem}")
            return mem
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse Redis memory data for phone number {phone_number}: {str(e)}")
            return {"long_term_memory": ["Error retrieving memory"]}

    # If not in Redis, retrieve from MongoDB
    LOGGER.info(f"No Redis cache found. Querying MongoDB for phone number: {phone_number}")
    user_data = await collection.find_one({"phone_number": phone_number}, {"_id": 0, "long_term_memory": 1})

    if user_data and "long_term_memory" in user_data:
        LOGGER.info(f"Found memory in MongoDB for phone number: {phone_number}")
        memory = user_data["long_term_memory"]
        LOGGER.info(f"The memory is {memory}")
        try:
            # Store in Redis with expiry
            await redis_client.setex(redis_key, REDIS_EXPIRY, json.dumps(memory))
            LOGGER.info(f"Successfully cached MongoDB memory in Redis for phone number: {phone_number}")
            return memory
        except Exception as e:
            LOGGER.error(f"Failed to cache MongoDB memory in Redis for phone number {phone_number}: {str(e)}")
            return memory

    LOGGER.info(f"No existing memory found. New user detected: {phone_number}")
    return {"long_term_memory" : ["No previous memory, New user"]}

async def store_memory(phone_number: str, new_messages: dict, timers: dict):
    """
    Stores short-term memory in Redis for fast retrieval.
    Resets the timer on new messages. Transfers long-term memory to MongoDB after 10 min of inactivity.
    """
    LOGGER.info(f"Starting memory storage process for phone number: {phone_number}")
    redis_key = f"user_memory:{phone_number}"
    last_message_key = f"last_message:{phone_number}"

    # Retrieve existing short-term memory from Redis
    LOGGER.info(f"Retrieving existing memory from Redis for key: {redis_key}")
    existing_memory_json = await redis_client.get(redis_key)
    
    try:
        existing_memory = json.loads(existing_memory_json) if existing_memory_json else {"long_term_history":[] ,"short_term_memory": []}
        LOGGER.info(f"Successfully parsed existing memory for phone number: {phone_number}")
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse existing memory for phone number {phone_number}: {str(e)}")
        existing_memory = {"long_term_history":[] ,"short_term_memory": []}
 
    # Process new messages
    LOGGER.info(f"Processing {len(new_messages)} new messages for phone number: {phone_number}")
    existing_memory["short_term_memory"].extend(new_messages["short_term_memory"])
    LOGGER.info(f"Added new short-term memory for phone number: {phone_number}")
    
    # LOGGER.info(f"new memory is {existing_memory}")
    now_timestamp = datetime.utcnow().timestamp()
    try:
        async with redis_client.pipeline() as pipe:
            pipe.setex(redis_key, REDIS_EXPIRY, json.dumps(existing_memory))
            pipe.set(last_message_key, now_timestamp, ex=REDIS_EXPIRY)
            await pipe.execute()
            LOGGER.info(f"Successfully stored memory in Redis for phone number: {phone_number}")
    except Exception as e:
        LOGGER.error(f"Failed to store memory in Redis for phone number {phone_number}: {str(e)}")

    # Reset and start a new timer
    if phone_number in timers:
        LOGGER.info(f"Cancelling existing timer for phone number: {phone_number}")
        timers[phone_number].cancel()
    
    LOGGER.info(f"Creating new memory transfer timer for phone number: {phone_number}")
    timers[phone_number] = asyncio.create_task(schedule_mongo_transfer(phone_number))

async def schedule_mongo_transfer(phone_number: str):
    """
    Waits for 10 minutes of inactivity before transferring long-term memory from Redis to MongoDB.
    """
    LOGGER.info(f"Starting memory transfer scheduler for phone number: {phone_number}")
    await asyncio.sleep(REDIS_EXPIRY)  # 10 minutes delay
    LOGGER.info(f"Waking up after {REDIS_EXPIRY} seconds for phone number: {phone_number}")

    redis_key = f"user_memory:{phone_number}"
    last_message_key = f"last_message:{phone_number}"

    # Retrieve last message timestamp
    last_timestamp = await redis_client.get(last_message_key)
    if last_timestamp and (datetime.utcnow().timestamp() - float(last_timestamp)) < REDIS_EXPIRY:
        LOGGER.info(f"Recent activity detected for phone number: {phone_number}, skipping transfer")
        return

    # Retrieve memory from Redis
    LOGGER.info(f"Retrieving memory from Redis for transfer, phone number: {phone_number}")
    existing_memory_json = await redis_client.get(redis_key)
    if not existing_memory_json:
        LOGGER.info(f"No memory found in Redis for transfer, phone number: {phone_number}")
        return

    try:
        existing_memory = json.loads(existing_memory_json)
        LOGGER.info(f"Successfully parsed memory for transfer, phone number: {phone_number}")
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse memory for transfer, phone number {phone_number}: {str(e)}")
        return

    # Extract long-term history only
    short_term_memory = existing_memory.get("short_term_memory", [])
    LOGGER.info(f"Extracting long-term memory for phone number: {phone_number}")
    to_be_saved_memory = await extract_long_term_memory(short_term_memory)
    LOGGER.info(f"The memory to for long term future edits {to_be_saved_memory}")
    if to_be_saved_memory:
        LOGGER.info(f"Transferring memory to MongoDB for phone number: {phone_number}")
        await transfer_long_term_to_mongo(phone_number, to_be_saved_memory)

    # Remove from Redis
    try:
        async with redis_client.pipeline() as pipe:
            pipe.delete(redis_key)
            pipe.delete(last_message_key)
            await pipe.execute()
            LOGGER.info(f"Successfully cleaned up Redis keys for phone number: {phone_number}")
    except Exception as e:
        LOGGER.error(f"Failed to clean up Redis keys for phone number {phone_number}: {str(e)}")

async def transfer_long_term_to_mongo(phone_number: str, to_be_saved_memory: list[str]):
    """
    Transfers long-term memory to MongoDB.
    """
    if not to_be_saved_memory:
        LOGGER.info(f"No memory to transfer for phone number: {phone_number}")
        return

    try:
        # Update or insert memory into MongoDB
        LOGGER.info(f"Starting MongoDB update for phone number: {phone_number}")
        await collection.update_one(
            {"phone_number": phone_number},
            {"$push": {"long_term_history": {"$each": to_be_saved_memory}}},
            upsert=True
        )
        LOGGER.info(f"Successfully transferred memory to MongoDB for phone number: {phone_number}")
    except Exception as e:
        LOGGER.error(f"Failed to transfer memory to MongoDB for phone number {phone_number}: {str(e)}")

async def extract_long_term_memory(short_term_memory: list[str]) -> list[str]:
    """
    Extracts long-term memory from short-term memory.
    """
    LOGGER.info("Starting long-term memory extraction")
    LOGGER.info(f"Processing {len(short_term_memory)} short-term memory items")
    parser = PydanticOutputParser(pydantic_object=Memory_Structured_Output)
    temp = PromptTemplate(template=MEMORY_PROMPT, partial_variables={"format_instructions": parser.get_format_instructions()} )
    message = temp.format(session_conversation=short_term_memory)
    
    try:
        LOGGER.info("Invoking LLM for memory extraction")
        strucuted_llm = LLM.with_structured_output(Memory_Structured_Output)
        response = await strucuted_llm.ainvoke(message)
        if response:
            LOGGER.info("Successfully extracted long-term memory")
            return [response.long_term_memory]
        LOGGER.warning("No content returned from LLM during memory extraction")
        return False
    except Exception as e:
        LOGGER.error(f"Failed to extract long-term memory: {str(e)}")
        return False
        
