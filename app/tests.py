from Agent.whatsapp_agent import Whatsapp_Agent
import asyncio
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from config import GROQ_API_KEY

llm = ChatGroq(api_key=GROQ_API_KEY,model="llama-3.1-70b-versatile")
Agent = Whatsapp_Agent(llm_dict={"Groq":llm})

Graph = Agent.graph

async def workflow(query: str):
    user_query = HumanMessage(content=query)
    response = []
    try:
        # Use `astream` to get async generator
        res = Graph.astream({"user_query": user_query}, stream_mode="messages")
        async for event in res:
            node = event[1].get('langgraph_node')
            if node == "Final":
                response.append(event[0].content)
                yield event[0].content
    
    except Exception as e:
        print(f"There was some error while getting response from the Groq LLM -> {e}")

asyncio.run(workflow("hello can you tell me the best policiy for my case"))