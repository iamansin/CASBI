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
from app.Utils.prompts import MAIN_PROMPT, FINAL_PROMPT, CALCULATOR_PROMPT
from app.Tools.RAGTool.rag_tool import get_fandqs, get_policy_recommendation, get_services
from app.Tools.REPLTool.repl_tool import Run_Python_Script


class Whatsapp_Agent:
    
    def __init__(self, llm_dict: dict):
        self._llm_dict = llm_dict
        self._tool_map = {
            "Recommendation_tool": self.Recommendation_tool,
            "FAQ_tool": self.FAQ_tool,
            "Services_tool": self.Services_tool,
            "Calculator_tool": self.Calculator_tool
        }
        self.graph = self.compile_graph()
        
    def compile_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("Thinker_node",self.Thinker_node)
        graph_builder.add_node("Validation_node",self.Validation_node)
        graph_builder.add_node("ToolManager_node",self.ToolManager_node)
        graph_builder.set_entry_point("Thinker_node")
        graph_builder.add_edge("Thinker_node","ToolManager_node")
        graph_builder.add_edge("ToolManager_node","Validation_node")
        graph_builder.add_conditional_edges("Validation_node", self.Router ,{
            "think_more": "Thinker_node",
            "end": END,
        })
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
    
    async def Thinker_node(self, state :AgentState):
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
        state.setdefault("selected_tools", []).append(response.selected_tools)
        state.setdefault("primary_objective", []).append(response.primary_objective)
        LOGGER.info("STATE updated now forwarding to next node")
        return state
    
    async def execute_tools(self, state :AgentState, tool :str, tool_query :str) -> dict:
        """
        Executes the selected tool based on the tool name and query.

        Args:
            state: The current AgentState.
            tool: The name of the tool to execute (string).
            tool_query: The query or input for the tool (string).

        Returns:
            A dictionary containing the results from the tool execution,
            or an error dictionary if the tool is not found.
        """
        tool_function = self._tool_map.get(tool)

        if tool_function:
            print(f"Executing tool: {tool} with query: {tool_query}")
            try:
                # **Invoke the tool function, passing state and tool_query**
                tool_result = await tool_function(state, tool_query) # Correctly invoke the async function
                tool_result["tool_name"] = tool # Ensure tool_name is in the result (if not already)
                return tool_result
            except Exception as e:
                LOGGER.error(f"Error executing tool '{tool}': {e}")
                return {"tool_name": tool, "error": e} # Return error info
        else:
            error_message = f"Tool '{tool}' not found in tool dictionary."
            print(error_message)
            return {"tool_name": tool, "error": error_message} # Return error info

    async def ToolManager_node(self, state:AgentState):
        selected_tool_list = state["selected_tools"][-1]
        tool_query = state["message"].content
        
        print(f"ToolManager_node: Selected tools: {selected_tool_list}, Query: {tool_query}")

        tool_tasks = [self.execute_tools(state, tool, tool_query) for tool in selected_tool_list]

        # Use asyncio.gather to run tool executions concurrently 
        tool_results_list = await asyncio.gather(*tool_tasks)

        tools_result_dict = {}
        for result in tool_results_list:
            tool_name = result.get("tool_name") # Assuming execute_tools returns dict with "tool_name"
            if tool_name: 
                tools_result_dict[tool_name] = result

        # Update the state with the aggregated tool results
        updated_state = state.update(tools_result=tools_result_dict) # Use state.update for cleaner updates
        print(f"ToolManager_node: Updated state with tool results: {tools_result_dict}")
        return updated_state
    
    async def Validation_node(self, state:AgentState):
        if state["tool_redirect"]:
            state["final_response"] = "this is the final node"
            return state
        
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
    
    # async def Router(self,state : AgentState):
    #     selected_tool_dict = state["selected_tools"][-1]
    #         # Ensure we only pick tools from step_1
    #     tools_to_run = selected_tool_dict.get("step_1", [])

    #     LOGGER.info(f"Routing to tools from step_1: {tools_to_run}")

    #     return tools_to_run if tools_to_run else "final_tool"
        
        
    async def Recommendation_tool(self,state:AgentState, tool_query:str):
        try:
            resutls  = await get_policy_recommendation(tool_query)
            LOGGER.info("Successfully got result from the Recommendation tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(resutls)
        return state
    
    async def FAQ_tool(self,state:AgentState, tool_query:str):
        try:
            resutls  = await get_fandqs(tool_query)
            LOGGER.info("Successfully got result from the FAQs tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(resutls)
        return state
    
    async def Services_tool(self,state:AgentState, tool_query:str):
        try:
            resutls  = await get_services(tool_query)
            formatted_result = []
            for doc in resutls:
                formatted_result.append(f"service : {doc.content} , solution : {doc.metadata['solution']}")
                
            LOGGER.info("Successfully got result from the Services tool")
        except Exception as e:
            LOGGER.error(f"There was some error while getting response from the tool  : {e}")
            resutls = ["Not able to get the results right now"]
        state.setdefault("tool_result", []).append(formatted_result)
        return state
    
    async def Calculator_tool(self,state:AgentState, tool_query:str):
        result = {}
        parser = PydanticOutputParser(pydantic_object=Calculator_Tool_Structure)
        template = PromptTemplate(
                                    template=CALCULATOR_PROMPT,
                                    partial_variables={"format_instructions": parser.get_format_instructions()},
                                )
        llm_message = template.format(user_message = tool_query, user_memory = state["user_long_term_memory"], session_memory = state["user_short_term_memory"] )
        response = await self.get_structured_response(llm_message,Calculator_Tool_Structure)
        
        function = response.function
        arguments = response.parameters
        need_more_info = response.need_more_info
        LOGGER.info(f"Function : {function} and arguments : {arguments}")
        if need_more_info:
            LOGGER.info("Need more information to run the function")
            need_parameters = response.need_parameters
            LOGGER.info(f"Need more information about the parameters {need_parameters}")
            result["need_parameters"] = need_parameters
            result["function_status"] = {"function" : function, "parameters": arguments}
            return result
        
        LOGGER.info("having all the information to run the function")
        val = await Run_Python_Script(function=function, args_dict=arguments)
        result["value"] = val
        result["parameter_used"] = {"function" : function, "parameters": arguments}
        return result