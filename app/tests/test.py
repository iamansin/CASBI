import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.Agent.whatsapp_agent import Whatsapp_Agent
from langchain_groq import ChatGroq
from app.Agent.agent_state import AgentState
from langchain_core.messages import HumanMessage, ToolMessage
import asyncio
import time 
from langchain_core.runnables.config import RunnableConfig
from app.Utils.config import GROQ_API_KEY
groq = ChatGroq(api_key = GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.0)
llm_dict = {"Groq":groq,}
agent = Whatsapp_Agent(llm_dict=llm_dict)


async def testing_function(state):
    start = time.time()
    res = await agent.graph.ainvoke(state, stream_mode="values")
    print(res)
    print(res.get("final_response", "No response"))

    print(f"Time taken to execute the function is {time.time()-start}")

query = "how much does it cost to smoke 10 cigarettes per day for 1 year if each pack costs 100 rupees and each pack contains 20 cigarettes?"

state : AgentState = {
    "message" : HumanMessage(content=query),
    "user_long_term_memory" : ["User's Name is Aman, he is single not married. He is an AI developer at SBI Bank. He lives in rajasthan jaipur."],
    "user_short_term_memory" : ["User greets with 'Hi' or 'Hello'."],
    "tool_redirect" : False,
}      
asyncio.run(testing_function(state))
