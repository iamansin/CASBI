from fastapi import APIRouter, Request, HTTPException
import json
from config import VERIFY_TOKEN,PHONE_NUMBER_ID
from utils import send_whatsapp_message, download_media
from input_processor import process_audio_input, process_image_input
from logger import LOGGER
from Agent.whatsapp_agent import Whatsapp_Agent


router = APIRouter()

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
    LOGGER.info(f"Received payload: {json.dumps(payload, indent=2)}")

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
                message_from = message.get("from", "")
                
                if message_from == PHONE_NUMBER_ID:
                    LOGGER.info(f"Skipping bot's own message: {message}")
                    continue 

                if msg_type == "text":
                    agent_input = message.get("text", {}).get("body", None)
                    LOGGER.info(f"Received text from {sender_id}: {agent_input}")

                elif msg_type == "image":
                    image_id = message.get("image", {}).get("id", "")
                    LOGGER.info(f"Received image from {sender_id}, Image ID: {image_id}")
                    file_path = await download_media(image_id)
                    agent_input = await process_image_input(file_path)
                    

                elif msg_type == "audio":
                    audio_id = message.get("audio", {}).get("id", "")
                    LOGGER.info(f"Received voice note from {sender_id}, Audio ID: {audio_id}")
                    file_path = await download_media(audio_id)
                    agent_input = await process_audio_input(file_path) 
                
                message = None
                
                if agent_input:
                    message = agent(agent_input)
                    
                
                await send_whatsapp_message(sender_id, message)

    return {"status": "received"}
