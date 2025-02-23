from fastapi import APIRouter, Request, HTTPException
import json
import time 
from Utils.config import VERIFY_TOKEN,PHONE_NUMBER_ID, GROQ_API_KEY
from Utils.message_handler import send_whatsapp_message
from Utils.input_processor import download_and_process
from Utils.memory_handler import retrieve_memory, store_memory
from Utils.logger import LOGGER
from Agent.whatsapp_agent import Whatsapp_Agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Initialize the agent
groq_mistral = ChatGroq(api_key = GROQ_API_KEY, model="llama-3.3-70b-specdec", temperature=0.0)
groq_llama = ChatGroq(api_key=GROQ_API_KEY,model="deepseek-r1-distill-llama-70b")
llm_dict = {"main_llm":groq_mistral, "fall_back_llm": groq_llama }
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
    LOGGER.info(f"Received payload: {payload}")

    # Ensure it's a valid WhatsApp message
    for entry_data in payload.get("entry", []):
        for change_data in entry_data.get("changes", []):
            value_data = change_data.get("value", {})
            messages_list = value_data.get("messages", [])

            if not messages_list:  # Optimization 1: Early exit if no messages
                LOGGER.debug("No messages found in payload, likely a status update or non-message event.")
                continue

            contacts_list = value_data.get("contacts", [{}])
            sender_id = contacts_list[0].get("wa_id", "Unknown")

            for message_data in messages_list:
                msg_type = message_data.get("type") # Directly get type
                message_from = message_data.get("from") # Directly get from

                if not msg_type or not message_from: # Optimization 2: Validate essential message info
                    LOGGER.warning(f"Incomplete message data received. Missing type or from. Message: {message_data}")
                    continue

                if message_from == PHONE_NUMBER_ID:
                    LOGGER.info(f"Skipping bot's own message: {message_data.get('id', 'No ID')}")
                    continue

                agent_input = None # Initialize outside if blocks for scope
                media_id = None    # Initialize outside if blocks for scope
                mime_type = None   # Initialize outside if blocks for scope

                if msg_type == "text":
                    agent_input = message_data.get("text", {}).get("body") # Direct access
                    if agent_input: # Check for None or empty body
                        LOGGER.info(f"Received text from {sender_id}: {agent_input[:50]}...") # Truncate log

                elif msg_type == "image":
                    media_id = message_data.get("image", {}).get("id")
                    if media_id: # Check for None or empty media_id
                        LOGGER.info(f"Received image from {sender_id}, Image ID: {media_id}")

                elif msg_type == "audio":
                    media_id = message_data.get("audio", {}).get("id")
                    if media_id: # Check for None or empty media_id
                        LOGGER.info(f"Received voice note from {sender_id}, Audio ID: {media_id}")

                elif msg_type == "document":
                    document_data = message_data.get("document", {}) # Get document dict once
                    media_id = document_data.get("id")
                    mime_type = document_data.get("mime_type")
                    file_name = document_data.get("filename")

                    if media_id and mime_type: # Optimization 3: Validate document data
                        LOGGER.info(f"Received document from {sender_id}, Filename: {file_name}, Mime Type: {mime_type}, Document ID: {media_id}")
                    else:
                        LOGGER.warning(f"Incomplete document data received. Missing media_id or mime_type. Document Data: {document_data}")
                        continue # Skip incomplete document

                elif msg_type: # Optimization 4: Handle unexpected but present msg_type
                    LOGGER.critical(f"Message type not supported: {msg_type} from {sender_id}. Message: {message_data}")
                    await send_whatsapp_message(sender_id, f"Message of type '{msg_type}' not supported.")
                    continue # Skip unsupported message


                if media_id and msg_type in ["audio", "image", "document"]: # Optimization 5: Combined condition
                    agent_input = await download_and_process(media_id, msg_type, mime_type) # Pass mime_type for document


                if agent_input:
                    # Retrieve user's long-term memory (rest of your logic remains the same)
                    try:
                        memory = await retrieve_memory(sender_id)
                        long_term_memory = " ".join(memory.get("long_term_memory", ["No previous memory, New user"]))
                        short_term_memory = " ".join(memory.get("short_term_memory", [""]))
                        print(f"The long_term_memory is {long_term_memory}")
                        print(f"The short_term_memory is {short_term_memory}")
                        initial_state = {"message": HumanMessage(content=agent_input), "user_long_term_memory" : long_term_memory,
                                                        "user_short_term_memory": short_term_memory,"tool_redirect":False}
                        try:
                            res = await agent.graph.ainvoke(initial_state, stream_mode="values")
                            message = res.get("final_response", None)
                            print(message)
                        except KeyError as e:
                            LOGGER.critical(f"Missing Key in agent invocation: {e}")
                        except Exception as e:
                            LOGGER.critical(e)

                    except Exception as e:
                        LOGGER.error(f"Error processing message: {e}")
                        message = None

                    await send_whatsapp_message(sender_id, message)
                    if message is not None:
                        new_mem = {"short_term_memory" : [ f" 'user : {agent_input} ,'assistant: {message} "] }
                        await store_memory(sender_id, new_mem, TIMERS)
            # else:
                # Optionally log status updates or handle them differently if needed
                # statuses = value.get("statuses", [])
                # if statuses:
                #     LOGGER.info(f"Received status update payload: {statuses}") # Log status updates for debugging


    return {"status": "received"}