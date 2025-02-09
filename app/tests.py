import asyncio
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connections():
    try:
        redis_client = aioredis.from_url("redis://localhost:6379")
        await redis_client.set("test_key", "Hello Redis")
        print("✅ Redis Connected:", await redis_client.get("test_key"))

        mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = mongo_client["test_db"]
        await db.test_collection.insert_one({"message": "Hello MongoDB"})
        doc = await db.test_collection.find_one({"message": "Hello MongoDB"})
        print("✅ MongoDB Connected:", doc)
    except Exception as e:
        print("❌ Connection Error:", e)

asyncio.run(test_connections())
