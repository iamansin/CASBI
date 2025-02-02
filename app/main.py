from fastapi import FastAPI
from webhook import router as webhook_router
import uvicorn

app = FastAPI(title="WhatsApp Chatbot API")

app.include_router(webhook_router)

@app.get("/")
async def root():
    return {"message": "WhatsApp Chatbot is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)