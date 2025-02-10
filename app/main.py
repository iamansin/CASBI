from fastapi import FastAPI
from webhook import router as webhook_router
import uvicorn
from connection_testing import DatabaseConnectionTester
from logger import LOGGER
import sys
app = FastAPI(title="WhatsApp Chatbot API")

app.include_router(webhook_router)

@app.on_event("startup")
async def startup_event():
    """
    Run database connection tests during application startup
    """
    LOGGER.info("Starting database connection verification...")
    try:
        tester = DatabaseConnectionTester()
        status = await tester.check_db_status()
        
        if status:
            LOGGER.info("***** Database connections verified successfully *****")
        else:
            LOGGER.error("XXXXX Database connection verification failed XXXXX")
            sys.exit(1)
            
    except Exception as e:
        LOGGER.error(f"Failed to verify database connections: {str(e)}")
        sys.exit(1)

@app.get("/")
async def root():
    return {"message": "WhatsApp Chatbot is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)