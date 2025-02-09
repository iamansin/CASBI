import asyncio
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connections():
    try:
        redis_client = aioredis.from_url("redis://localhost:6379")
        await redis_client.set("test_key", "Hello Redis")
        print("✅ Redis Connected:", await redis_client.get("test_key"))
        
        mongo_client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
        db = mongo_client["memory_store"]  # Database: memory_store
        collection = db["user_memory"]  # Collection: user_memory
        
        # Insert Test Data
        await collection.insert_one({"phone_number": "1234567890", "memory": ["Hello MongoDB"]})
        doc = await collection.find_one({"phone_number": "1234567890"})
        print("✅ MongoDB Connected:", doc)
    except Exception as e:
        print("❌ Connection Error:", e)

asyncio.run(test_connections())


async def check_data():
    mongo_client = AsyncIOMotorClient("mongodb://127.0.0.1:27017")
    db = mongo_client["memory_store"]
    collection = db["user_memory"]

    doc = await collection.find_one({})
    print("🔍 Found in MongoDB:", doc)

asyncio.run(check_data())

async def check_redis_data():
    redis_client = aioredis.from_url("redis://localhost:6379")

    value = await redis_client.get("test_key")
    if value:
        print("✅ Data found in Redis:", value.decode("utf-8"))
    else:
        print("❌ Data not found in Redis")

    await redis_client.close()

# Run the function
asyncio.run(check_redis_data())