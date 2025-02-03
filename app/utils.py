import httpx
import logging
import aiofiles
import os
from config import ACCESS_TOKEN, PHONE_NUMBER_ID, VERSION

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

async def send_whatsapp_message(recipient_id: str, text: str | None):
    """
    Sends a WhatsApp message to a user.
    """
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    if text is None:
        text = "We are unable to process your request right now. Please Try again Later!"
        
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=HEADERS, json=payload)
        logging.info(f"Sent message to {recipient_id}: {text} | Status: {response.status_code}")

    return response.json()


async def download_media(media_id: str, save_dir: str = "downloads"):
    """
    Downloads media (image/audio) from WhatsApp servers using the media ID and saves it locally.
    """
    # Step 1: Get the direct media URL
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch media URL: {response.status_code}")
            return None

        media_data = response.json()
        media_url = media_data.get("url")

    if not media_url:
        logging.error("Media URL not found.")
        return None

    logging.info(f"Downloading media from: {media_url}")

    # Step 2: Download the media file
    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, headers=HEADERS)

        if response.status_code != 200:
            logging.error(f"Failed to download media: {response.status_code}")
            return None

        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)

        # Determine file extension
        content_type = response.headers.get("Content-Type", "")
        file_extension = content_type.split("/")[-1]  # Extract file format (e.g., jpg, png, mp3)

        # Save file
        file_path = os.path.join(save_dir, f"{media_id}.{file_extension}")

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(response.content)

    logging.info(f"Media saved at: {file_path}")
    return file_path