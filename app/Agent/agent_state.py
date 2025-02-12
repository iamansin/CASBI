from typing_extensions import Annotated, List, TypedDict, Dict, Any, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,ToolMessage
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    message : HumanMessage
    understanding : List[str] 
    selected_tools : List[Dict] 
    primary_objective : List[str]
    execution_sequence : List[List[str]]
    user_long_term_memory : str
    user_short_term_memory : str
    final_response : str
    tool_redirect : bool



class ToolExecutionPlan(BaseModel):
    """
    Defines the execution strategy for handling user queries by selecting and sequencing tools.
    """

    understanding: str = Field(description="Concise analysis of the user's core need")

    selected_tools: Dict[
        Literal['F-AND-Q', 'Customer-Care-Agents-Department', 'Policy-Recommendation', 'Human-Interupt', 'Final-Node'],
        str
    ] = Field(
        description="Tools required to solve the query with their execution order. Tools with the same step number will be executed in parallel.\n"
                    "\n🔹 **Customer-Care-Agents-Department** → Use only for user complaints or requests that need human customer care assistance."
                    "\n🔹 **Policy-Recommendation** → Use only if the user expresses interest in policy recommendations."
                    "\n🔹 **F-AND-Q (Frequently Asked Questions Database)** → Use only if the user’s question closely matches FAQs. Do not use for casual greetings."
                    "\n🔹 **Human-Interupt** → Use only when more user input is needed before proceeding."
                    "\n🔹 **Final-Node** → Use this as default for simple responses (e.g., greetings, acknowledgments, confirmations)."
    )

    primary_objective: str = Field(description="Clear outcome-focused goal statement")

    execution_sequence: List[str] = Field(description="Ordered steps for optimal resolution")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "understanding": "User wants to file a claim for a car accident.",
                    "selected_tools": {
                        "F-AND-Q": "step_1",  # FAQs about claims process
                        "Customer-Care-Agents-Department": "step_2",  # Connect to agent
                        "Final-Node": "step_3"  # End conversation
                    },
                    "primary_objective": "Guide the user through the initial steps of filing a claim and connect them with an agent.",
                    "execution_sequence": [
                        "1. Provide FAQs about the claims process.",
                        "2. Connect the user with a customer care agent.",
                        "3. End the conversation."
                    ]
                },
                {
                "understanding": "User is looking for a new life insurance policy.",
                "selected_tools": {
                    "Policy-Recommendation": "step_1",  # Recommend life insurance policies
                    "F-AND-Q": "step_2",  # Answer questions about policy options
                    "Human-Interupt": "step_3",  # For complex questions or customization
                    "Final-Node": "step_4"  # End conversation
                },
                "primary_objective": "Guide the user through life insurance options and connect them with a human agent if needed.",
                "execution_sequence": [
                    "1. Recommend suitable life insurance policies based on user needs.",
                    "2. Answer user questions about the recommended policies using FAQs.",
                    "3. If the user has complex questions or needs customization, transfer them to a human agent.",
                    "4. End the conversation."
                ]
                },
                {
                    "understanding": "User greets with 'Hi' or 'Hello'.",
                    "selected_tools": {
                        "Final-Node": "step_1"
                    },
                    "primary_objective": "Acknowledge the user's greeting with a friendly response.",
                    "execution_sequence": [
                        "1. Respond with a simple greeting and end the conversation."
                    ]
                },
                {
                    "understanding": "User is looking to update their policy coverage.",
                    "selected_tools": {
                        "Policy-Recommendation": "step_1",  # Recommend coverage options
                        "F-AND-Q": "step_2",  # Answer questions about changes
                        "Human-Interupt": "step_3",  # For complex changes
                        "Final-Node": "step_4"  # End conversation
                    },
                    "primary_objective": "Help the user explore coverage options and escalate to a human agent if needed.",
                    "execution_sequence": [
                        "1. Recommend relevant policy coverage options.",
                        "2. Answer user questions using FAQs.",
                        "3. If complex changes are needed, transfer to a human agent.",
                        "4. End the conversation."
                    ]
                },
                {
                    "understanding": "User asks 'What is your name?'.",
                    "selected_tools": {
                        "Final-Node": "step_1"
                    },
                    "primary_objective": "Provide a direct answer without using any tool.",
                    "execution_sequence": [
                        "1. Respond with the bot's name and end the conversation."
                    ]
                },
                {
                    "understanding": "User needs assistance with understanding their policy terms.",
                    "selected_tools": {
                        "F-AND-Q": "step_1",  # Provide FAQs
                        "Human-Interupt": "step_2",  # For complex explanations
                        "Final-Node": "step_3"  # End conversation
                    },
                    "primary_objective": "Provide clear explanations of policy terms, escalating to a human if necessary.",
                    "execution_sequence": [
                        "1. Provide relevant FAQs about policy terms.",
                        "2. If the user needs further assistance, connect them with a human agent.",
                        "3. End the conversation."
                    ]
                },
                {
                    "understanding": "User wants to know the status of their submitted application.",
                    "selected_tools": {
                        "F-AND-Q": "step_1",  # Answer questions about application status
                        "Customer-Care-Agents-Department": "step_2",  # Connect to agent for specific queries
                        "Final-Node": "step_3"  # End conversation
                    },
                    "primary_objective": "Provide application status information and offer support through a customer care agent.",
                    "execution_sequence": [
                        "1. Answer FAQs about application status and processing times.",
                        "2. If the user has specific questions, connect them with a customer care agent.",
                        "3. End the conversation."
                    ]
                },
                {
                    "understanding": "User is interested in learning about investment options related to their insurance policy.",
                    "selected_tools": {
                        "Policy-Recommendation": "step_1",  # Recommend relevant policies with investment options
                        "F-AND-Q": "step_2",  # Answer questions about investment options
                        "Human-Interupt": "step_3",  # Transfer to human agent for complex investment advice
                        "Final-Node": "step_4"  # End conversation
                    },
                    "primary_objective": "Educate the user on investment-linked insurance policies and offer human agent support.",
                    "execution_sequence": [
                        "1. Recommend relevant insurance policies with investment options.",
                        "2. Answer user questions about the investment options using FAQs.",
                        "3. If the user needs complex investment advice, transfer them to a human agent.",
                        "4. End the conversation."
                    ]
                }
            ]
        }

class Output_Structure(BaseModel):
    response : str =Field(description="This field contains final results.")
    
class Memory_Structured_Output(BaseModel):
    long_term_memory : str | None = Field(description="This field contains the long term memory that has been extracted from the session converstation.")
    
    