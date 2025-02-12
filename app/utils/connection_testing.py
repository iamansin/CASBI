import logging
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis
from datetime import datetime

# Setup logging
LOGGER = logging.getLogger(__name__)

class DatabaseConnectionTester:
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.mongo_url = "mongodb://127.0.0.1:27017"
        self.test_data = {
            "test_id": "connection_test",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active"
        }
        self.redis_test_key = "connection_test_key"
        
    async def test_connections(self):
        """Test both Redis and MongoDB connections by inserting test data."""
        try:
            # Initialize connections
            LOGGER.info("Initializing database connections")
            self.redis_client = aioredis.from_url(self.redis_url)
            self.mongo_client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.mongo_client["memory_store"]
            self.collection = self.db["user_memory"]

            # Test Redis Connection
            LOGGER.info("Testing Redis connection")
            await self.redis_client.set(
                self.redis_test_key, 
                str(self.test_data),
                ex=300  # 5 minutes expiry
            )
            LOGGER.info("Successfully inserted test data into Redis")

            # Test MongoDB Connection
            LOGGER.info("Testing MongoDB connection")
            await self.collection.insert_one(self.test_data)
            LOGGER.info("Successfully inserted test data into MongoDB")

            LOGGER.info("All database connections established successfully")
            return True

        except Exception as e:
            LOGGER.error(f"Connection test failed: {str(e)}")
            return False

    async def verify_redis_data(self):
        """Verify Redis data and clean up test data."""
        try:
            LOGGER.info("Verifying Redis test data")
            redis_client = aioredis.from_url(self.redis_url)
            value = await redis_client.get(self.redis_test_key)
            
            if value:
                LOGGER.info("Successfully retrieved test data from Redis")
                # Clean up test data
                await redis_client.delete(self.redis_test_key)
                LOGGER.info("Successfully cleaned up Redis test data")
                await redis_client.close()
                return True
            else:
                LOGGER.error("Test data not found in Redis")
                return False

        except Exception as e:
            LOGGER.error(f"Redis verification failed: {str(e)}")
            return False

    async def verify_mongo_data(self):
        """Verify MongoDB data and clean up test data."""
        try:
            LOGGER.info("Verifying MongoDB test data")
            mongo_client = AsyncIOMotorClient(self.mongo_url)
            db = mongo_client["memory_store"]
            collection = db["user_memory"]

            # Find test document
            doc = await collection.find_one({"test_id": "connection_test"})
            
            if doc:
                LOGGER.info("Successfully retrieved test data from MongoDB")
                # Clean up test data
                await collection.delete_one({"test_id": "connection_test"})
                LOGGER.info("Successfully cleaned up MongoDB test data")
                return True
            else:
                LOGGER.error("Test data not found in MongoDB")
                return False

        except Exception as e:
            LOGGER.error(f"MongoDB verification failed: {str(e)}")
            return False

    async def check_db_status(self):
        """Complete database health check workflow."""
        try:
            LOGGER.info("Starting database health check")
            
            # Step 1: Test initial connections and insert data
            connection_status = await self.test_connections()
            if not connection_status:
                LOGGER.error("Initial connection test failed")
                return False

            # Step 2: Verify Redis data and cleanup
            redis_status = await self.verify_redis_data()
            if not redis_status:
                LOGGER.error("Redis verification failed")
                return False

            # Step 3: Verify MongoDB data and cleanup
            mongo_status = await self.verify_mongo_data()
            if not mongo_status:
                LOGGER.error("MongoDB verification failed")
                return False

            LOGGER.info("Database health check completed successfully")
            return True

        except Exception as e:
            LOGGER.error(f"Database health check failed: {str(e)}")
            return False

# Usage example
async def check_db_health():
    tester = DatabaseConnectionTester()
    status = await tester.check_db_status()
    if status:
        LOGGER.info("***** All database connections are healthy *****")
    else:
        LOGGER.error("XXXXX Database connection check failed XXXXX")

