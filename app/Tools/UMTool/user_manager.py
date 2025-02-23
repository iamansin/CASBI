import aiosqlite
import asyncio

async def get_user_details(phone_number: str):
    async with aiosqlite.connect("user_data.db") as conn:
        cursor = await conn.cursor()

        # Check if user exists
        await cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        user = await cursor.fetchone()

        if not user:
            return {"error": "User not found"}

        # Fetch user's policies
        await cursor.execute("SELECT policy_id, policy_name, payment_status FROM policies WHERE phone_number = ?", (phone_number,))
        policies = await cursor.fetchall()

        return {
            "phone_number": user[0],
            "name": user[1],
            "nominee": user[2],
            "policies": [
                {"policy_id": p[0], "policy_name": p[1], "payment_status": p[2]}
                for p in policies
            ]
        }

# Example Usage
async def main():
    phone = "+918306639922"
    user_details = await get_user_details(phone)
    print(user_details)

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
