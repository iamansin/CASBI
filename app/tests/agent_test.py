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
llm_dict = {"main_llm":groq}
agent = Whatsapp_Agent(llm_dict=llm_dict)


async def testing_function(state):
    start = time.time()
    res = await agent.graph.ainvoke(state, stream_mode="values")
    for key,val in res.items():
        print("*"*10)
        print(f"{key} : {val}")


    print(f"Time taken to execute the function is {time.time()-start}")

query = "can you please suggest me some policies?"

state : AgentState = {
    "message" : HumanMessage(content=query),
    "user_long_term_memory" : ["User's Name is Aman, he is single not married. He is an AI developer at SBI Bank. He lives in rajasthan jaipur. User is a smoker."],
    "user_short_term_memory" : [" 'user' : 'hi , 'assistant' : 'hello how may i help you today' , 'user' : 'i was thinking of getting some policy', 'assistant' : 'Sure i am right here to help you in selecting best policies for you, tell me more specificly so that i can help you better.' , 'user' : 'but firstly i was thinking of getting some calcuations about my self so as to know which policy to take, i smoke very much i think that i might affect my decision.', 'assistance' : 'ok sir ill get back to you.'' "],
    "tool_redirect" : False,
}      
asyncio.run(testing_function(state))
