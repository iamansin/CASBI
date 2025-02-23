from groq import Groq
import aiofiles
import os
import httpx
import PyPDF2
import io
from docx import Document 
import tempfile
from .config import GROQ_API_KEY
from .logger import LOGGER
import aiofiles
import base64
from pathlib import Path
import time 
from .config import ACCESS_TOKEN

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
Groq_Client = Groq(api_key=GROQ_API_KEY)

async def download_and_process(media_id: str, media_type: str, mime_type : str | None = None):
    """
    Downloads media (image/audio) from WhatsApp servers using the media ID and saves it locally.
    """
    # Step 1: Get the direct media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            LOGGER.error(f"Failed to fetch media URL: {response.status_code}")
            return None

        media_data = response.json()
        media_url = media_data.get("url")

    if not media_url:
        LOGGER.error("Media URL not found.")
        return None

    LOGGER.info(f"Downloading media from: {media_url}")

    # Step 2: Download the media file
    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, headers=HEADERS)

        if response.status_code != 200:
            LOGGER.error(f"Failed to download media: {response.status_code}")
            return None

        # Determine file extension
        content_type = response.headers.get("Content-Type", "")
        file_extension = content_type.split("/")[-1]  # Extract file format (e.g., jpg, png, mp3)
        
        try :
            LOGGER.info("Creating new temp file for the media..")
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, f"{media_id}.{file_extension}")

                async with aiofiles.open(temp_file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)

                if media_type == "image":
                    text = await process_image_input(temp_file_path)
                elif media_type == "document": 
                    text = await process_document_input(temp_file_path, mime_type)
                elif media_type == "audio": 
                    text = await process_audio_input(temp_file_path)
                else:
                    LOGGER.warning(f"Unknown media type for processing: {media_type}")
                    text = "Unsupported media type." 
                
        except Exception as e:
            LOGGER.error(f"Error processing media file: {e}")
            text = None
    # LOGGER.info(f"Processed text: {text}")
    return text

async def process_audio_input(audio_file_path : str):
    """This Function will take audio file as an input,
    and process it for extracting information.
    audio_file : str (path for audio to be processed) 
    """
    start_time = time.time()
    LOGGER.info(f"Processing audio file for user {audio_file_path}...")
 
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription_result = Groq_Client.audio.transcriptions.create(
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
        return None

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
    
    LOGGER.info("Sending request to the model")
    response_time = time.time()
    try:
        completion = Groq_Client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You Are and Whatsapp AI Assistant. Your task is to understand the content of the image and provide a brief description of it. You must understand and provide you thoughts for the same."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded_image}"
                        }
                    }
                ]
            }
                ],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=False,
            )


        LOGGER.info(f"Time taken to process the image:{time.time() - start_time}, Model response time : {time.time()- response_time}")
        return completion.choices[0].message.content

    except Exception as e:
        LOGGER.error(f"Error processing image file: {e}")
        return None
    
async def process_document_input(document_file_path: str, mime_type: str):
    """This function will take document as input and process it,
    for extracting information.
    document : str (path for document to be processed)
    """
    start_time = time.time()
    LOGGER.info(f"Processing document file {document_file_path}...")
    try:
        if mime_type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(document_file_path)
                text = ""   
                if len(pdf_reader.pages) > 3:
                    return "The Document is too long cannot parse it !"
                for page_num in range(len(pdf_reader.pages)): 
                    page = pdf_reader.pages[page_num] 
                    text += page.extract_text()
                LOGGER.info(f"Time taken to process the PDF: {time.time() - start_time}")
                return text
        elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            word_document = Document(document_file_path)
            text = ""
            for paragraph in word_document.paragraphs:
                text += paragraph.text + "\n"
            LOGGER.info(f"Time taken to process the Word document: {time.time() - start_time}")
            return text
        else:
            LOGGER.warning(f"Unsupported document type: {mime_type}")
            return "Unsupported document type."
    except Exception as e:
        LOGGER.error(f"Error processing document file: {e}")

