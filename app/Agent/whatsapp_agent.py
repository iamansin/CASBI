from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from logger import LOGGER
import json
import asyncio
from langchain.runnables import RunnableConfig
from agent_state import AgentState
from typing_extensions import List
from pydantic import BaseModel, Field
from prompts import MAIN_PROMPT, FINAL_PROMPT

class Thought_Structure(BaseModel):
    tool_list : List[str] = Field(description="This field contains a list of tool/tools which are to be used right now.")
    thought : str = Field(description= "This field contains initial plan.")
    
class Output_Structure(BaseModel):
    pass
    


class Whatsapp_Agent:
    def __init__(self, llm_dict: dict, tool_list : List | None):
        self._llm_dict = llm_dict,
        self._tool_dict = {tool.name: tool for tool in tool_list} if tool_list is not None else {},
        self.graph = self.compile_graph()
        self.history = self.get
        
    def compile_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("main_node",self.main_node)
        graph_builder.add_node("search_vector_store", self.search_vector_store)
        graph_builder.add_conditional_edges("main_node", self.router, {
            "vectore_store" : "search_vector_store"
        })
        return graph_builder.compile() 
    
    async def get_structured_response(self, message: str, output_structure : BaseModel):
        """
        Get a structured response from the LLM with retries.
        
        Args:
            message (str): The input message to the LLM.

        Returns:
            JSONStructOutput: The structured output from the LLM if successful.
        
        Raises:
            RuntimeError: If all retry attempts fail.
        """
        llm_structured = self._llm_dict["Groq"].with_structured_output(output_structure)
        
        for attempt in range(1,4):
            try:
                LOGGER.info(f"Attempt {attempt}: Invoking LLM")
                structured_response = llm_structured.ainvoke(message)
                LOGGER.warning(f"The response recieved from LLM in structured format ---> {structured_response}")
                if structured_response:
                    return structured_response
                continue
            except Exception as e:
                LOGGER.error(f"Attempt {attempt} failed: {str(e)}")
                LOGGER.info("Retrying...")
        # If all retries fail, raise an exception
        LOGGER.critical("Failed to get a structured response from the LLM after 3 attempts.")
        raise RuntimeError("Failed to get a structured response from the LLM after 3 attempts.")
    
    
    async def main_node(self, state :AgentState, config :RunnableConfig):
        
        #Initially getting the long term memory from Redis/mongoDB
        long_term_history = await self.get_user_history(phone_number = config["phone_number"])
        state["user_long_term_history"] = long_term_history
        
        #Checking if the request is direct or redirected from any tool
        if state["tool_redirect"]:
            last_tool_update =  state["tool_result"][-1]
            tool_result = [result.content for result in last_tool_update] if len(last_tool_update) > 1 else last_tool_update[0].content
            pass
        
        text_message = state["message"]
        parser = PydanticOutputParser(pydantic_object=Thought_Structure)
        template = PromptTemplate(
                                    template=MAIN_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(user_message = text_message)
        response = await self.get_structured_response(llm_message,Thought_Structure)
        state["tools"]= response.tool_list
        state["plan"] = response.thought
        return state
                
                
    async def search_vector_store(self, state:AgentState):
        pass
    
    async def final_node(self, state:AgentState):
        message = state["message"]
        long_term_history = state["user_long_term_history"]
        session_history = state["user_short_term_history"]
        parser = PydanticOutputParser(pydantic_object=Output_Structure)
        template = PromptTemplate(
                                    template=FINAL_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(long_term_history = long_term_history, session_history = session_history, user_message = message)
        response = await self.get_structured_response(llm_message,Output_Structure)
        
        
        
        
    