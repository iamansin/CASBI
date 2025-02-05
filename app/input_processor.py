from groq import Groq
from config import GROQ_API_KEY, HF_TOKEN
from prompts import IMAGE_PROMPT
from huggingface_hub import InferenceClient
import aiofiles
import base64
from pathlib import Path
import time 
from logger import LOGGER

Audio_Client = Groq(api_key=GROQ_API_KEY)
Image_Client = InferenceClient(
	provider="hf-inference",
	api_key=HF_TOKEN)


async def process_audio_input(audio_file_path : str):
    """This Function will take audio file as an input,
    and process it for extracting information.
    audio_file : str (path for audio to be processed) 
    """
    start_time = time.time()
    LOGGER.info(f"Processing audio file for user {audio_file_path}...")
 
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription_result = Audio_Client.audio.transcriptions.create(
                file=(audio_file_path, audio_file),
                model="whisper-large-v3",
                language="en"
            ) 
        text = transcription_result.text.strip()
        print(f"Time taken to process the audio: {time.time()-start_time}")
        LOGGER.info("Successfully processed audio file.")
        return text
    
    except Exception as e:
        LOGGER.error(f"Error processing audio file: {e}")
        return "Error processing audio file. Please try again."

async def process_image_input(image_file_path : str):
    """This function will take image as input and process it,
    for extracting information.
    image : str (path for image to be processed)
    """
    start_time =  time.time()
    async with aiofiles.open(image_file_path, mode='rb') as file:
            image_data = await file.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        # Determine MIME type based on file extension
    extension = Path(image_file_path).suffix.lower()
    mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }.get(extension, 'image/jpeg')

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": IMAGE_PROMPT,
                    
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{encoded_image}",
                    }
                }
            ]
        }
    ]
    LOGGER.info("Sending request to the model")
    response_time = time.time()
    try:
        completion = Image_Client.chat.completions.create(
            model="meta-llama/Llama-3.2-11B-Vision-Instruct", 
            messages=messages, 
            max_tokens=500
        )
        LOGGER.info(f"Time taken to process the image:{time.time() - start_time}, Model response time : {time.time()- response_time}")
        return completion.choices[0].message.content

    except Exception as e:
        LOGGER.error(f"Error processing image file: {e}")
        return "Error processing image file. Please try again."

