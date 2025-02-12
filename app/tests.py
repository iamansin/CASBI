from Agent.agent_memory import retrieve_memory, store_memory
from Agent.agent_state import AgentState
import time
import asyncio

TIMERS = {}
phone_number = "918307789732"

async def mock_agent_response(state:AgentState):
    state : AgentState = {
    "message" : state["message"],
    "understanding" : ["User greets with 'Hi' or 'Hello'."],
    "selected_tools" : [{'Final-Node': 'step_1'}],
    "user_long_term_history" : state["user_long_term_memory"],
    "primary_objective" : ["Acknowledge the user's greeting with a friendly response."],
    "execution_sequence" : [['1. Respond with a simple greeting and end the conversation.']],
    "user_short_term_history" : state["user_short_term_memory"],
    "tool_redirect" : False,
    "final_response" : f"recieved your response : {state["message"]}"
    }
    
    return state
    

async def memory_testing( query: str, phone_number : str = "918307789732"):
    
    mem = await retrieve_memory(phone_number)
    long_m = " ".join(mem.get("long_term_memory",["No memory, new user"]))
    short_m = " ".join(mem.get("short_term_memory",[""]))
    print(f"This is the retrieved long term memory :{long_m}")
    print(f"This is the retrieved short term memory: {short_m} ")
    initial_state = {"message": query, "user_long_term_memory" : long_m, "user_short_term_memory": short_m}
    response = await mock_agent_response(initial_state)
    message = response.get("final_response","No respose recieved!")
    conv =  {"short_term_memory" : [f" 'user': {query} ,\n 'assistant': {message} "]}
    response  = await store_memory(phone_number, conv, TIMERS)
    await asyncio.sleep(20)
 
def main():
    query_idict = {
        # "1" : "when are my policies alvailable",
        # "2" : "my name is utkarsh gupta",
        "3" : "im a student of srm college",
        # "4" : "i have 2 cars",
        # "5" : "my daughter is JPHS school",
        # "6" : "hi",
        # "7" : "My comapnay is a startup",
        # "8" : "my father's name is ravi gupta",
        # "9" : "i need help",
        # "10" : "how are you",
    }
    for key, values in query_idict.items():
        print(f"{key} Running for : {values}")
        asyncio.run(memory_testing(values))
        
print("Starting testing...")

main()# def test_memory_testing():
#     import pytest
    
#     # Test case 1: New user with no memory
#     async def test_new_user():
#         test_phone = "911234567890"
#         test_query = "Hi"
#         result = await memory_testing(test_phone, test_query)
        
#         assert isinstance(result, dict)
#         assert result["message"] == test_query
#         assert "No memory, new user" in result["user_long_term_memory"]
#         assert result["user_short_term_memory"] == ""
#         assert result["final_response"] == f"recieved your response : {test_query}"

#     # Test case 2: User with existing memory
#     async def test_existing_user():
#         # First store some memory
#         await store_memory(phone_number, ["Previous conversation"], ["Recent interaction"])
        
#         result = await memory_testing(phone_number, "Hello")
        
#         assert isinstance(result, dict)
#         assert result["message"] == "Hello"
#         assert "Previous conversation" in result["user_long_term_memory"]
#         assert "Recent interaction" in result["user_short_term_memory"]
#         assert result["final_response"] == "recieved your response : Hello"

#     # Run the async tests
#     import asyncio
#     asyncio.run(test_new_user())
#     asyncio.run(test_existing_user())
    
