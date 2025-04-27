import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from Tools.UMTool.user_manager import get_user_details
import asyncio

async def generate_link(policies: list):
    payment_links = {}
    for policy in policies:
        payment_links[policy["policy_name"]] = f"https://policy_payment_{policy['policy_id']}/gateway/secured/"
    return payment_links


async def get_payment_link(phone_number: str) -> dict:
    """
    Retrieves the user's due policies and generates payment links.

    Args:
        phone_number (str): The user's phone number.

    Returns:
        dict: Contains the user's name and a list of due policies with payment links.
    """
    try:
        user_details = await get_user_details(phone_number)

        if "error" in user_details:
            return {"error": "User not found. Please check the phone number."}

        # Extract due policies
        due_policies = [p for p in user_details["policies"] if p["payment_status"].upper() == "DUE"]

        if not due_policies:
            return {"message": f"All policies are paid for {user_details['name']}."}

        # Generate payment links
        payment_links = await generate_link(due_policies)

        return {
            "user": user_details["name"],
            "due_policies": payment_links
        }

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Example Usage
async def main():
    phone = "+918306639922"
    result = await get_payment_link(phone)
    print(result)

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())