from fastapi import APIRouter, Request, HTTPException
import json
from config import VERIFY_TOKEN,PHONE_NUMBER_ID, GROQ_API_KEY
from utils import send_whatsapp_message, download_media
from input_processor import process_audio_input, process_image_input
from logger import LOGGER
from Agent.whatsapp_agent import Whatsapp_Agent
from Agent.agent_memory import retrieve_memory, store_memory
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Initialize the agent
groq = ChatGroq(api_key = GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.0)
llm_dict = {"Groq":groq,}
agent = Whatsapp_Agent(llm_dict=llm_dict)
TIMERS = {}

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
                    # Retrieve user's long-term memory
                    try:
                        memory = await retrieve_memory(sender_id)
                        long_term_memory = memory.get("long_term_memory", ["No previous memory, New user"])
                        short_term_memory = memory.get("short_term_memory", [""])
                        
                        initial_state = {"message": HumanMessage(content=agent_input), "user_long_term_history" : long_term_memory,
                                        "short_term_memory": short_term_memory,"tool_redirect":False}
                        
                        res = await agent.graph.ainvoke(initial_state, stream_mode="values")
                        message = res.get("final_response", None)
                        LOGGER.info(f"Response from agent: {message}")
                            
                    except Exception as e:
                        LOGGER.error(f"Error processing message: {e}")
                        message = None

                await send_whatsapp_message(sender_id, message)
                new_mem = {"long_term_memory" : long_term_memory, "short_term_memory" : [agent_input + message] }
                await store_memory(sender_id, new_mem, TIMERS)

    return {"status": "received"}
