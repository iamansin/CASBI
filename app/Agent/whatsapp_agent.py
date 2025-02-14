import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.Utils.logger import LOGGER
import time
import json
import asyncio
from typing_extensions import List 
from pydantic import BaseModel
from .agent_state import AgentState, ToolExecutionPlan, Output_Structure, Calculator_Tool_Structure
from app.Utils.prompts import MAIN_PROMPT, FINAL_PROMPT, TOOL_PROMPT
from app.Tools.RAGTool.rag_tool import get_fandqs, get_policy_recommendation, get_services
from app.Tools.REPLTool.repl_tool import Run_Python_Script


class Whatsapp_Agent:
    
    def __init__(self, llm_dict: dict, tool_list : List | None = None):
        self._llm_dict = llm_dict
        self._tool_dict = {tool.name: tool for tool in tool_list} if tool_list is not None else {},
        self.graph = self.compile_graph()
        
    def compile_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("Main_node",self.Main_node)
        graph_builder.add_node("Final_node",self.Final_node)
        graph_builder.add_node("Service_node",self.Services_tool_node)
        graph_builder.add_node("FAQ_node",self.FAQ_tool_node)
        graph_builder.add_node("Calculator_node",self.Calculator_tool_node)
        graph_builder.add_node("Recommendation_node",self.Recommendation_tool_node)
        graph_builder.set_entry_point("Main_node")
        graph_builder.add_conditional_edges("Main_node", self.main_node_router ,{
            "service_tool": "Service_node",
            "fandq_tool": "FAQ_node",
            "recommendation_tool": "Recommendation_node",
            "calculator_tool": "Calculator_node",
            "final_tool": "Final_node",
        })
        graph_builder.add_edge("FAQ_node","Main_node")
        graph_builder.add_edge("Recommendation_node","Main_node")
        graph_builder.add_edge("Service_node","Main_node")
        graph_builder.add_edge("Calculator_node","Main_node")
        graph_builder.add_edge("Final_node",END)
        graph = graph_builder.compile() 
        return graph 
    
    async def get_structured_response(self, message: str, output_structure : BaseModel):
        """Get a structured response from the LLM with retries.
        Args:
            message (str): The input message to the LLM.
        Returns:
            JSONStructOutput: The structured output from the LLM if successful.
        Raises:
            RuntimeError: If all retry attempts fail.
        """

        # start_time = time.time()
        llm_structured = self._llm_dict["Groq"].with_structured_output(output_structure)
        
        for attempt in range(1,4):
            try:
                LOGGER.info(f"Attempt {attempt}: Invoking LLM")
                structured_response = await llm_structured.ainvoke(message)
                if structured_response:
                    # print(f"Time taken to get the structured response is {time.time()-start_time}")
                    return structured_response
                continue
            except Exception as e:
                LOGGER.error(f"Attempt {attempt} failed: {str(e)}")
                LOGGER.info("Retrying...")
        # If all retries fail, raise an exception
        LOGGER.critical("Failed to get a structured response from the LLM after 3 attempts.")
        
        raise RuntimeError("Failed to get a structured response from the LLM after 3 attempts.")
    
    
    async def Main_node(self, state :AgentState):
        """This is the main entry node for the 
        Args:
            state (AgentState) : This the state that has to be passed on 
            config (RunnablConfig) : This parameter takes config which has user phone number.
        Returns:
            """
        #Checking if the request is direct or redirected from any tool
        if state["tool_redirect"]:
            last_tool_update =  state["tool_result"][-1]
            tool_result = [result.content for result in last_tool_update] if len(last_tool_update) > 1 else last_tool_update[0].content
            pass
        
        #If the message to the direct entry point.
        text_message = state["message"].content
        parser = PydanticOutputParser(pydantic_object=ToolExecutionPlan)
        template = PromptTemplate(
                                    template=MAIN_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(user_message = text_message, user_memory = state["user_long_term_memory"], session_memory = state["user_short_term_memory"] )
        LOGGER.info("Recieved response from the model.")
        #Getting response from the LLM
        response = await self.get_structured_response(llm_message,ToolExecutionPlan)
        state.setdefault("understanding", []).append(response.understanding)
        state.setdefault("selected_tools", []).append(response.selected_tools)
        state.setdefault("primary_objective", []).append(response.primary_objective)
        state.setdefault("execution_sequence", []).append(response.execution_sequence)
        LOGGER.info("STATE updated now forwarding to next node")
        return state
    
    async def Final_node(self, state:AgentState):
        message = state["message"].content
        long_term_memory = state["user_long_term_memory"]
        session_memory = state.get("user_short_term_memory", " ")
        primary_objective = state["primary_objective"][-1]
        execution_plan = " ".join(state["execution_sequence"][-1]) 
        parser = PydanticOutputParser(pydantic_object=Output_Structure)
        template = PromptTemplate(
                                    template=FINAL_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(long_term_memory = long_term_memory, session_memory = session_memory, 
                                      user_message = message, objective = primary_objective, execution_plan = execution_plan)
        response = await self.get_structured_response(llm_message,Output_Structure)
        state["final_response"] = response.response
        return state
    
    async def main_node_router(self,state : AgentState):
        selected_tool_dict = state["selected_tools"][-1]
            # Ensure we only pick tools from step_1
        tools_to_run = selected_tool_dict.get("step_1", [])

        LOGGER.info(f"Routing to tools from step_1: {tools_to_run}")

        return tools_to_run if tools_to_run else "final_tool"
        
        
    async def Recommendation_tool_node(self,state:AgentState):
        tool_query = state["tool_query"]
        try:
            resutls  = await get_policy_recommendation(tool_query)
            LOGGER.info("Successfully got result from the Recommendation tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(resutls)
        return state
    
    async def FAQ_tool_node(self,state:AgentState):
        tool_query = state["tool_query"]
        try:
            resutls  = await get_fandqs(tool_query)
            LOGGER.info("Successfully got result from the FAQs tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(resutls)
        return state
    
    async def Services_tool_node(self,state:AgentState):
        tool_query = state["tool_query"]
        try:
            resutls  = await get_policy_recommendation(tool_query)
            LOGGER.info("Successfully got result from the Services tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(resutls)
        return state
    
    async def Calculator_tool_node(self,state:AgentState):
        parser = PydanticOutputParser(pydantic_object=Calculator_Tool_Structure)
        template = PromptTemplate(
                                    template=CALCULATOR_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(tool_query = state["tool_query"], user_memory = state["user_long_term_memory"], session_memory = state["user_short_term_memory"] )
        response = await self.get_structured_response(llm_message,Output_Structure)
        
        function = response.get("function",None)
        arguments = response.get("parameters", None)
        need_more_info = response.get("more_info", True)
        
        if need_more_info:
            pass
        
        result = await Run_Python_Script(function=function, args_dict=arguments)
        state.setdefault(["tool_result"],[]).append([result])