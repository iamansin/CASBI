import httpx
from .config import PHONE_NUMBER_ID, VERSION,ACCESS_TOKEN
from .logger import LOGGER
ACCESS_TOKEN="EAAdMNBkxpuoBO7iiBLSQhsGSMNBGz3Mk5RnAtrainuAIaIxYRBp7KCcj0Cbs3XIULZBFjQ6mZCNmawpkHfWqt000NTxuc5P8eBNKrDpyrZCkwyVHQxsw3JcQQgndBtqkH9X9Q0gFykWt9mmc9jsemiv8HvynbhxRM0ZCUlg0yT0ZASg0PK18eoGQdDteuCAfiQlmD3DzRXdZCiMBF2PkZBa0mq4ZCr0HRPzftXEZD"
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
        "text": {"body": text.strip()}
    }
    try :
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=HEADERS, json=payload)
            # print(response.status_code, response.text)
            LOGGER.info(f"Sent message to {recipient_id}| Status: {response.status_code}")
    
    except Exception as e:
        print(f"There was some error while sending the request back to the user : {e}")

    return response.json()


