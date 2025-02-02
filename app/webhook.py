from fastapi import APIRouter, Request, HTTPException
import logging
import json
from config import VERIFY_TOKEN
from utils import send_whatsapp_message, download_media

router = APIRouter()

logging.basicConfig(filename="./logs/app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta calls this endpoint for verification during setup.
    """
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")
    
    if token == VERIFY_TOKEN:
        return int(challenge)  # Required to complete webhook setup
    
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def receive_message(request: Request):
    """
    Handles incoming WhatsApp messages.
    """
    payload = await request.json()
    logging.info(f"Received payload: {json.dumps(payload, indent=2)}")

    # Ensure it's a valid WhatsApp message
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            # Get sender details (if available)
            contacts = value.get("contacts", [{}])
            sender_id = contacts[0].get("wa_id", "Unknown")

            # Process incoming messages
            messages = value.get("messages", [])
            for message in messages:
                msg_type = message.get("type", "")

                if msg_type == "text":
                    text = message.get("text", {}).get("body", "")
                    logging.info(f"Received text from {sender_id}: {text}")

                elif msg_type == "image":
                    image_id = message.get("image", {}).get("id", "")
                    logging.info(f"Received image from {sender_id}, Image ID: {image_id}")
                    await download_media(image_id)

                elif msg_type == "audio":
                    audio_id = message.get("audio", {}).get("id", "")
                    logging.info(f"Received voice note from {sender_id}, Audio ID: {audio_id}")
                    await download_media(audio_id)

                # Send acknowledgment response
                await send_whatsapp_message(sender_id, "Got your message!")

    return {"status": "received"}
