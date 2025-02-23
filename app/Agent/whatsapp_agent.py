import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.Utils.logger import LOGGER
import asyncio
from pydantic import BaseModel
from .agent_state import (AgentState, Initial_Output_Structure, 
                          Final_Output_Structure, Final_Tool_Structure,
                          Thinker_Output_Structure, Calculator_Tool_Structure, Observer_Output_Structure)
from app.Utils.prompts import MAIN_PROMPT, FINAL_PROMPT, CALCULATOR_PROMPT, FINAL_TOOL_PROMPT, THINKER_PROMPT, OBSERVER_PROMPT
from app.Tools.RAGTool.rag_tool import get_fandqs, get_policy_recommendation, get_services
from app.Tools.REPLTool.repl_tool import Run_Python_Script


class Whatsapp_Agent:
    
    def __init__(self, llm_dict: dict):
        self._llm_dict = llm_dict
        self._tool_map = {
            "recommendation_tool": self.Recommendation_tool,
            "fandq_tool": self.FAQ_tool,
            "service_tool": self.Services_tool,
            "calculator_tool": self.Calculator_tool
        }
        self.graph = self.compile_graph()
        
    def compile_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("Thinker_node",self.Thinker_node)
        graph_builder.add_node("Observer_node",self.Observer_node)
        graph_builder.add_node("Validation_node",self.Validation_node)
        graph_builder.add_node("ToolManager_node",self.ToolManager_node)
        graph_builder.set_entry_point("Observer_node")
        graph_builder.add_edge("Thinker_node","ToolManager_node")
        graph_builder.add_edge("ToolManager_node","Validation_node")
        graph_builder.add_conditional_edges("Observer_node", self.Flow_Router, {
            "thinker_node" : "Thinker_node",
            "final_node": "Validation_node"
        })
        graph_builder.add_conditional_edges("Validation_node", self.Router ,{
            "think_more": "Thinker_node",
            "end": END,
        })
        graph = graph_builder.compile() 
        return graph 
    
    async def get_structured_response(self, output_structure : BaseModel, PROMPT : str, **kwargs):
        """Get a structured response from the LLM with retries.
        Args:
            message (str): The input message to the LLM.
        Returns:
            JSONStructOutput: The structured output from the LLM if successful.
        Raises:
            RuntimeError: If all retry attempts fail.
        """
        parser = PydanticOutputParser(pydantic_object=output_structure)
        template = PromptTemplate(template= PROMPT, partial_variables={"format_instructions": parser.get_format_instructions()},)
        message = template.format(**kwargs)
        llm_structured = self._llm_dict["main_llm"].with_structured_output(output_structure)
        
        for attempt in range(1,4):
            try:
                LOGGER.info(f"Attempt {attempt}: Invoking LLM")
                structured_response = await llm_structured.ainvoke(message)
                if structured_response:
                    return structured_response
                continue
            except Exception as e:
                LOGGER.error(f"Attempt {attempt} failed: {str(e)}")
                LOGGER.info("Retrying...")
        # If all retries fail, raise an exception
        LOGGER.critical("Failed to get a structured response from the LLM after 3 attempts.")
        fall_back_llm = self._llm_dict["fall_back_llm"].with_structured_output(output_structure)
        LOGGER.info("Using Fall Back LLM.")
        try:
            structured_response = await fall_back_llm.ainvoke(message)
            if structured_response:
                LOGGER.info(f"Recieved result is : {structured_response}")
                return structured_response
        except Exception as e:
            LOGGER.error(f"Attempt failed: {str(e)}")
            raise RuntimeError("Failed to get a structured response from the LLM after 3 attempts.")

    async def Observer_node(self, state:AgentState):
        user_message = state["message"].content
        long_term_memory = state["user_long_term_memory"]
        session_memory = state["user_short_term_memory"]
        
        response = await self.get_structured_response(Observer_Output_Structure, OBSERVER_PROMPT, long_term_memory = long_term_memory,
                                                session_memory = session_memory, user_message = user_message)
        
        state["next_node"] = response.next_node 
        state["prompt"] = response.prompt
        state["tool_query"] = response.tool_query
        print(f"NEXT NODE : {response.next_node} ")
        print(f" PROMPT : {response.prompt}")
        print(f"TOOL_query : {response.tool_query}")
        return state
    
    async def Flow_Router(self, state : AgentState) :
        next_node = state["next_node"]
        if next_node == "thinker_node":
            return "thinker_node"
        return "final_node"
    
    async def Thinker_node(self, state: AgentState) -> AgentState:
        """This is the main entry node for the agent's thinking process.............................................................
        

        This function determines whether the user's request is a direct query
        or a follow-up after a tool execution. It then constructs an appropriate
        prompt, calls the LLM for structured output, and updates the agent's state
        accordingly.

        Args:
            state (AgentState): The current state of the agent, containing
                user message, memory, tool redirection flag, and other relevant data.

        Returns:
            AgentState: The updated agent state after the thinking process.
        """
        # LOGGER.info("Inside thinker node")
        text_message = state["message"].content
        tool_redirect = state["tool_redirect"]
        prompt = state["prompt"]
        if tool_redirect:  # Request is a follow-up after tool execution
                try:
                    last_tool_results = state["last_tool_results"][-1]
                    thought = state["thought"]
                    primary_objective = state["primary_objective"]
                    response = await self.get_structured_response(Thinker_Output_Structure, THINKER_PROMPT,
                                                                user_message=text_message, last_tool_results=last_tool_results,
                                                                thought=thought, primary_objective=primary_objective, )
                    
                    state["selected_tools"].append(response.selected_tools)

                except (KeyError, IndexError) as e:  # Handle state access errors
                    LOGGER.error(f"Error accessing state variables: {e}")
                    raise e
                except Exception as e: # Handle any other exception during tool redirection
                    LOGGER.error(f"Error during tool redirection logic: {e}")
                    raise e

        else: 
                try:
                    response = await self.get_structured_response(Initial_Output_Structure, MAIN_PROMPT,
                                                                user_message=text_message, prompt = prompt)
                    
                    state.setdefault("selected_tools",[]).append(response.selected_tools)
                    state["primary_objective"] = response.primary_objective
                    print(f"selected tool : {response.selected_tools}")
                    print(f"primary objective : {response.primary_objective}")
                except Exception as e: # Handle any other exception during direct request
                    LOGGER.error(f"Error during direct request processing: {e}")
                    raise e

        # LOGGER.info("State updated now forwarding to next node")
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
        LOGGER.info(f"Running evalution for the tool : {tool}")
        tool_function = self._tool_map.get(tool)

        if tool_function:
            LOGGER.info(f"Executing tool: {tool} with query: {tool_query}")
            try:
                # **Invoke the tool function, passing state and tool_query**
                tool_result = await tool_function(state, tool_query) # Correctly invoke the async function
                return {tool : tool_result}
            except Exception as e:
                LOGGER.error(f"Error executing tool '{tool}': {e}")
                return {"tool_name": tool, "error": e} # Return error info
        else:
            error_message = f"Tool '{tool}' not found in tool dictionary."
            LOGGER.info(error_message)
            return {"tool_name": tool, "error": error_message} # Return error info

    async def ToolManager_node(self, state:AgentState):
        selected_tool_list = state["selected_tools"][-1]
        tool_query = state["message"].content
        
        LOGGER.info(f"ToolManager_node: Selected tools: {selected_tool_list}, Query: {tool_query}")
        if selected_tool_list[0] == "final_tool":
            return state
        tool_tasks = [self.execute_tools(state, tool, tool_query) for tool in selected_tool_list]

        # Use asyncio.gather to run tool executions concurrently 
        tool_results_list = await asyncio.gather(*tool_tasks)

        tools_result_dict = {tool : result[tool] for tool, result in zip(selected_tool_list, tool_results_list)}

        # Update the state with the aggregated tool results
        state["tool_results"] = tools_result_dict
        LOGGER.info(f"ToolManager_node: Updated state with tool results: {tools_result_dict}")
        state["tool_redirect"] = True
        return state
    
    async def Validation_node(self, state: AgentState) -> AgentState:
        """
        Validates the agent's state and decides the next node in the LangGraph flow.

        This node checks if tools were used in the previous step (`state.tool_redirect`).
        If tools were used, it formats the tool results and prompts the LLM (via `get_structured_response`)
        to validate the results and decide if more thinking is needed.
        If no tools were used, it directly prompts the LLM to generate the final response.

        Args:
            state (AgentState): The current agent state, including:
                - tool_redirect (bool): Indicates if tools were used in the prior step.
                - selected_tools (List[List[str]]): List of selected tool names if tools were used.
                - tool_result (Dict[str, dict]): Dictionary of tool results if tools were used.
                - message (Any): User message content.
                - user_long_term_memory (str): Long-term memory content.
                - user_short_term_memory (str): Short-term memory content.
                - primary_objective (str): The primary objective of the agent.

        Returns:
            AgentState: The updated agent state, with:
                - next_node (str, optional): Set to "think_more" if LLM requests more thinking when tools are used.
                                            Set to "final_node" when no tools are used, indicating the final response node.
                - final_response (str, optional): Set to the LLM's final response when no tools are used.
        """
        LOGGER.info("Inside validation node")
        message = state["message"].content
        prompt = state["prompt"]
        
        tool_redirect = state["tool_redirect"] 
        if tool_redirect:
            results = []
            primary_objective = state["primary_objective"]
            selected_tools = state["selected_tools"][-1] # Access the last list of selected tools once
            tool_results = state["tool_results"] # Access tool_result dictionary once

            for tool_name in selected_tools: 
                result_dict = tool_results.get(tool_name)

                if result_dict: 
                    result_strings = [] 
                    for key, val in result_dict.items(): 
                        result_strings.append(f" {key} : {', '.join(val)}")
                    results.append(f"Results of {tool_name} are :[ { ' \n '.join(result_strings)} ]")
                else:
                    results.append(f"No results found for tool: {tool_name}") 

            results = " ".join(results)
            response = await self.get_structured_response(Final_Tool_Structure,FINAL_TOOL_PROMPT,
                                                        tool_results= results, prompt = prompt, user_message=message,
                                                        primary_objective=primary_objective) 

            if response.think_more:
                state.setdefault("last_tool_results",[]).append(results)
                print(response.thought)
                state["thought"] = response.thought
                state["next_node"] = "think_more" 
                return state 

        else: # No tool redirect path
            response = await self.get_structured_response(Final_Output_Structure, FINAL_PROMPT,
                                                        prompt = prompt,
                                                        user_message=message)

        state["final_response"] = response.response
        state["next_node"] = "final_node"
        return state 

    
    async def Router(self,state : AgentState):
        # LOGGER.info("INTO router node")
        next_node = state["next_node"]
        LOGGER.info(f"Next node is : {next_node}")
        if next_node == "think_more":
            return "think_more"
        return "end"
        
    async def Recommendation_tool(self, state: AgentState, tool_query: str) -> dict: 
        
        LOGGER.info(f"Recommendation_tool started for query: {tool_query}") 
        results_documents = []
        try:
            resutls = await get_policy_recommendation(tool_query) 
            LOGGER.info("Successfully got result from Recommendation tool")
        except Exception as e:
            LOGGER.error(f"Error getting response from Recommendation tool: {e}")
            return {"documents": ["Not able to get the results right now"]} 

        for doc in resutls:
            results_documents.append(f"policy : {doc.metadata["Policy Name"]} , policy-type : {doc.metadata["Type"]} , link : {doc.metadata["Policy URL"]} \n")

        # Always return a dictionary with "documents" key, list of documents (even if empty or single)
        return {"documents": results_documents} # Join documents into single string in list
    
    async def FAQ_tool(self, state: AgentState, tool_query: str) -> dict: 
        
        LOGGER.info(f"Recommendation_tool started for query: {tool_query}") 
        results_documents = []
        try:
            resutls = await get_fandqs(tool_query) 
            LOGGER.info("Successfully got result from FAQs tool")
        except Exception as e:
            LOGGER.error(f"Error getting response from FAQs tool: {e}")
            return {"documents": ["Not able to get the results right now"]} 

        for doc in resutls:
            results_documents.append(f"policy : {doc.page_content.strip()} \n") # .strip() for cleaner content

        # Always return a dictionary with "documents" key, list of documents (even if empty or single)
        return {"documents": results_documents} # Join documents into single string in list
    
    async def Services_tool(self, state: AgentState, tool_query: str) -> dict: 
        
        LOGGER.info(f"Recommendation_tool started for query: {tool_query}") 
        results_documents = []
        try: 
            resutls = await get_services(tool_query) 
            LOGGER.info("Successfully got result from the Services tool")
        except Exception as e:
            LOGGER.error(f"Error getting response from the Services tool: {e}")
            return {"documents": ["Not able to get the results right now"]} 

        for doc in resutls:
            results_documents.append(f"service : {doc.page_content} , solution : {doc.metadata['solution']} \n")

        # Always return a dictionary with "documents" key, list of documents (even if empty or single)
        return {"documents": results_documents} # Join documents into single string in list
    
    async def Calculator_tool(self, state: AgentState, tool_query: str) -> dict:
        """
        Executes the Calculator tool to perform calculations based on user query.

        This tool uses an LLM to parse the user query, extract the function to execute
        and its parameters, and then attempts to run a Python script to perform the calculation.

        Args:
            state (AgentState): The current agent state, including user memory.
            tool_query (str): The user's query related to calculation.

        Returns:
            Dict: A dictionary containing the result of the calculation or information
                  about missing parameters if more information is needed. The dictionary
                  can have the following keys:
                  - "value" (optional): The calculated value if the function execution was successful.
                  - "parameter_used" (str): String representation of the function and parameters used.
                  - "need_parameters" (optional): List of parameters needed if more information is required.
        """
        result = {}
        try:
            response = await self.get_structured_response(Calculator_Tool_Structure, CALCULATOR_PROMPT,
                                                            user_message=tool_query,
                                                            user_memory=state["user_long_term_memory"],
                                                            session_memory=state["user_short_term_memory"]) 

            function = response.function
            arguments = response.parameters
            need_more_info = response.need_more_info

            # LOGGER.info(f"Function : {function} and arguments : {arguments}")

            if need_more_info:
                LOGGER.info("Need more information to run the function")
                need_parameters = response.need_parameters
                # LOGGER.info(f"Need more information about the parameters {need_parameters}")
                result["need_parameters"] = need_parameters
                result["parameter_used"] = [f" 'function' : {function}, 'parameters' : {arguments}"]
                return result
            else:
                LOGGER.info("Having all the information to run the function")
                val = await Run_Python_Script(function=function, args_dict=arguments) 
                result["value"] = [val]
                result["parameter_used"] = [f" 'function' : {function}, 'parameters' : {arguments}"]
                return result 
            
        except Exception as e:
            LOGGER.error(f"There was some problem while getting response from the calculator tool : {e}")
            return {"result" : "Not able to get the results due to some problem"}