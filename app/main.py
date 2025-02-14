from fastapi import FastAPI
from webhook import router as webhook_router
import uvicorn
from Utils.connection_testing import DatabaseConnectionTester
from Utils.faiss_loader import load_faiss_retrievers
from Utils.logger import LOGGER
import sys
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan function to handle startup and shutdown events."""
    
    LOGGER.info("Starting database connection verification...")
    
    try:
        tester = DatabaseConnectionTester()
        status = await tester.check_db_status()

        if status:
            LOGGER.info("***** Database connections verified successfully *****")
        else:
            LOGGER.error("XXXXX Database connection verification failed XXXXX")
            sys.exit(1)

        # Load FAISS indexes once during startup
        await load_faiss_retrievers(
            policy_faiss_file="./app/faiss_indexes/policy_faiss_index",
            profile_faiss_file="./app/faiss_indexes/profile_faiss_index",
            fandq_faiss_file="./app/faiss_indexes/fandq_faiss_index",
            use_gpu=True  # Set False for CPU
        )
        LOGGER.info("***** FAISS indexes loaded successfully *****")

    except Exception as e:
        LOGGER.error(f"Failed during startup: {str(e)}")
        sys.exit(1)

    yield  # Keep the app running

app = FastAPI(title="WhatsApp Chatbot API", lifespan=lifespan)

app.include_router(webhook_router)

@app.get("/")
async def root():
    return {"message": "WhatsApp Chatbot is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)