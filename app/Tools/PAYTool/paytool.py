import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import uuid

async def get_payment_link(user_id : str) -> str:
    try:
        user_details = await get_user_details(user_id)
        if user_details:
            active_policies = user_details["active_policies"]
            if active_policies:
                due_pay_policies = [policy for policy in active_policies if policy["payment_status"] == "DUE"]
                payment_links = await generate_link(due_pay_policies)
                return payment_links
            return "The user do not have any current active policies. Ask if they are intreseted in buying in new one."
        return "New User, no previous data found"
    except Exception as e:
        return "There was some problem while getting details of the user please tell them to try again later."


async def generate_link(policies : dict) :
    payment_links = {}
    for policy in policies:
        id = str(uuid.uuid4())
        payment_links[policy["name"]] = f"https:/policy_payment_{policy["policy_id"]}/gateway/secured/"
    return payment_links