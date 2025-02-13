# from Agent.whatsapp_agent import Whatsapp_Agent
# from langchain_groq import ChatGroq
# from Agent.agent_state import AgentState
# from langchain_core.messages import HumanMessage, ToolMessage
# import asyncio
# import time 
# from langchain_core.runnables.config import RunnableConfig
# from app.utils.config import GROQ_API_KEY
# groq = ChatGroq(api_key = GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.0)
# llm_dict = {"Groq":groq,}
# agent = Whatsapp_Agent(llm_dict=llm_dict)
# state : AgentState = {
#     "message" : HumanMessage(content="hi!"),
#     "understanding" : ["User greets with 'Hi' or 'Hello'."],
#     "selected_tools" : [{'Final-Node': 'step_1'}],
#     "user_long_term_history" : ["User's Name is Aman, he is single not married. He is an AI developer at SBI Bank. He lives in rajasthan jaipur."],
#     "primary_objective" : ["Acknowledge the user's greeting with a friendly response."],
#     "execution_sequence" : [['1. Respond with a simple greeting and end the conversation.']],
#     "user_short_term_history" : ["User greets with 'Hi' or 'Hello'."],
#     "tool_redirect" : False,
# }

# async def testing_function(user_message: str):
#     config = {"configurable": {"user_number": 8306639922}}
#     start = time.time()
#     history = ["User's Name is Aman, he is single not married. He is an AI developer at SBI Bank. He lives in rajasthan jaipur."]

#     res = await agent.graph.ainvoke({"message": HumanMessage(content=user_message), "user_long_term_history" : history,"tool_redirect":False}, config, stream_mode="values")
#     print(res.get("final_response", "No response"))

#     print(f"Time taken to execute the function is {time.time()-start}")

    

# query = "hi"            
# asyncio.run(testing_function(query))
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
print("importing logger")
from app.Utils.logger import LOGGER