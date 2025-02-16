from typing_extensions import Annotated, List, TypedDict, Dict, Any, Literal
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    message : str
    understanding : List[str] 
    selected_tools : List[Dict] 
    primary_objective : List[str]
    execution_sequence : List[List[str]]
    user_long_term_memory : str
    user_short_term_memory : str   
    final_response : str
    tool_redirect : bool
    tool_query : str
    tool_result : List[List]
    need_parameters: List
    function_status: List
    parameters_used : List

class ToolExecutionPlan(BaseModel):
    """
    Defines the execution strategy for handling user queries by selecting and sequencing tools.
    """

    understanding: str = Field(description="Concise analysis of the user's core need")

    selected_tools: Dict[
        str,
        Literal['fandq_tool', 'service_tool', 'recommendation_tool', 'calculator_tool', 'final_tool']
    ] = Field(
        description="Tools required to solve the query with their execution order. Tools with the same step number will be executed in parallel.\n"
                    "\n🔹 **service_tool** → Use only for user complaints or requests that need human customer care assistance."
                    "\n🔹 **recommendation_tool** → Use only if the user expresses interest in policy recommendations."
                    "\n🔹 **fandq_tool(Frequently Asked Questions Database)** → Use only if the user’s question closely matches FAQs. Do not use for casual greetings."
                    "\n🔹 **calculator_tool** → Use only when there is a need to a calculate something or if the user specifically asks for some calculations."
                    "\n🔹 **final_tool** → Use this as default for simple responses (e.g., greetings, acknowledgments, confirmations)."
    )

    primary_objective: str = Field(description="Clear outcome-focused goal statement")

    execution_sequence: List[str] = Field(description="Ordered steps for optimal resolution")

    class Config:
        json_schema_extra = {
  "examples": [
    {
      "understanding": "User wants to file a claim for a car accident.",
      "selected_tools": {
        "step_1": "fandq_tool",
        "step_2": "service_tool",
        "step_3": "final_tool"
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
        "step_1": "recommendation_tool",
        "step_2": "fandq_tool",
        "step_3": "final_tool"
      },
      "primary_objective": "Guide the user through life insurance options and answer their questions.",
      "execution_sequence": [
        "1. Recommend suitable life insurance policies based on user needs.",
        "2. Answer user questions about the recommended policies using FAQs.",
        "3. End the conversation."
      ]
    },
    {
      "understanding": "User greets with 'Hi' or 'Hello'.",
      "selected_tools": {
        "step_1": "final_tool"
      },
      "primary_objective": "Acknowledge the user's greeting with a friendly response.",
      "execution_sequence": [
        "1. Respond with a simple greeting and end the conversation."
      ]
    },
    {
      "understanding": "User is looking to update their policy coverage.",
      "selected_tools": {
        "step_1": "recommendation_tool",
        "step_2": "fandq_tool",
        "step_3": "final_tool"
      },
      "primary_objective": "Help the user explore coverage options and answer their questions.",
      "execution_sequence": [
        "1. Recommend relevant policy coverage options.",
        "2. Answer user questions using FAQs.",
        "3. End the conversation."
      ]
    },
    {
      "understanding": "User asks 'What is your name?'.",
      "selected_tools": {
        "step_1": "final_tool"
      },
      "primary_objective": "Provide a direct answer without using any tool.",
      "execution_sequence": [
        "1. Respond with the bot's name and end the conversation."
      ]
    },
    {
      "understanding": "User needs assistance with understanding their policy terms.",
      "selected_tools": {
        "step_1": "fandq_tool",
        "step_2": "final_tool"
      },
      "primary_objective": "Provide clear explanations of policy terms.",
      "execution_sequence": [
        "1. Provide relevant FAQs about policy terms.",
        "2. End the conversation."
      ]
    },
    {
      "understanding": "User wants to know the status of their submitted application.",
      "selected_tools": {
        "step_1": "fandq_tool",
        "step_2": "service_tool",
        "step_3": "final_tool"
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
        "step_1": "recommendation_tool",
        "step_2": "fandq_tool",
        "step_3": "final_tool"
      },
      "primary_objective": "Educate the user on investment-linked insurance policies.",
      "execution_sequence": [
        "1. Recommend relevant insurance policies with investment options.",
        "2. Answer user questions about the investment options using FAQs.",
        "3. End the conversation."
      ]
    },
    {
      "understanding": "User wants to calculate smoking-related costs for their insurance.",
      "selected_tools": {
        "step_1": "calculator_tool",
        "step_2": "final_tool"
      },
      "primary_objective": "Calculate and explain the impact of smoking on insurance premiums.",
      "execution_sequence": [
        "1. Use the calculator to determine the additional cost due to smoking.",
        "2. Explain the results to the user.",
        "3. End the conversation."
      ]
    },
    {
      "understanding": "User wants to calculate the potential payout of their policy.",
      "selected_tools": {
        "step_1": "calculator_tool",
        "step_2": "final_tool"
      },
      "primary_objective": "Calculate and explain the potential policy payout.",
      "execution_sequence": [
        "1. Use the calculator to estimate the policy payout based on user input.",
        "2. Explain the results to the user.",
        "3. End the conversation."
      ]
    }

  ]
}

class Output_Structure(BaseModel):
    response : str =Field(description="This field contains final results.")
    
class Memory_Structured_Output(BaseModel):
    long_term_memory : str | None = Field(description="This field contains the long term memory that has been extracted from the session converstation.")
    
class Calculator_Tool_Structure(BaseModel):
    function : str = Field(description="This is the function that has to be called.")
    parameters : dict = Field(description="This dict contains the parameters as keys and their values")
    need_more_info :bool = Field(description="If the information is not enough to compile the parameters for the provided function. Then True else False")
    need_parameters : List[str] | None = Field(description="This field contains the parameters which are required ")
    class Config:
        json_schema_extra = {
  "examples": [
    {
  "examples": [
    {
      "user_message": "I want to know how much I'll spend on smoking over the next 5 years. I smoke about 10 cigarettes a day, a pack has 20 cigarettes, and a pack costs $10.",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "cost_of_smoking",
        "parameters": {
          "cigarettes_per_day": 10,
          "cigarettes_per_pack": 20,
          "price_per_pack": 10.0,
          "years_smoking": 5
        },
        "need_more_info": False,
        "need_paramters": None
      }
    },
    {
      "user_message": "How much will my savings of $500 per month be worth in 10 years if the return rate is 7%?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "future_value_of_monthly_savings",
        "parameters": {
          "monthly_savings": 500.0,
          "years": 10,
          "rate_of_return": 7.0
        },
        "need_more_info": False,
        "need_paramters": None
      }
    },
    {
      "user_message": "I have $10,000 invested.  How long will it take to double if I get a 6% return?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "time_to_double_money",
        "parameters": {
          "amount": 10000.0,
          "interest_rate": 6.0
        },
        "need_more_info": False,
        "need_paramters": None
      }
    },
    {
      "user_message": "What will the cost of a $200 item be in 3 years with 2% inflation?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "future_cost_planner",
        "parameters": {
          "current_cost": 200.0,
          "years": 3,
          "inflation_rate": 2.0
        },
        "need_more_info": False,
        "need_paramters": None
      }
    },
        {
      "user_message": "I'm thinking about starting to save, but I'm not sure how much I can save monthly. Can you help me plan?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "future_value_of_monthly_savings",
        "parameters": {},
        "need_more_info": True,
        "need_paramters": ["monthly_savings", "years", "rate_of_return"]
      }
    },
    {
      "user_message": "How much will I spend on cigarettes?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "cost_of_smoking",
        "parameters": {},
        "need_more_info": True,
        "need_paramters": ["cigarettes_per_day", "cigarettes_per_pack", "price_per_pack", "years_smoking"]
      }
    },
    {
      "user_message": "What will the cost of college be in the future?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "future_cost_planner",
        "parameters": {},
        "need_more_info": True,
        "need_paramters": ["current_cost", "years", "inflation_rate"]
      }
    },
    {
      "user_message": "How long until my investment doubles?",
      "user_long_term_memory": [],
      "session_memory": [],
      "output": {
        "function": "time_to_double_money",
        "parameters": {},
        "need_more_info": True,
        "need_paramters": ["amount", "interest_rate"]
      }
    },
    {
      "user_message": "I want to calculate my smoking costs, but I don't remember the price of a pack.",
      "user_long_term_memory": [
        {"cigarettes_per_day": 15},
        {"cigarettes_per_pack": 20},
        {"years_smoking": 10}
      ],
      "session_memory": [],
      "output": {
        "function": "cost_of_smoking",
        "parameters": {
          "cigarettes_per_day": 15,
          "cigarettes_per_pack": 20,
          "years_smoking": 10
        },
        "need_more_info": True,
        "need_paramters": ["price_per_pack"]
      }
    },
    {
      "user_message": "I'm planning for my retirement.  I save $1000/month. What will it be in 20 years?",
      "user_long_term_memory": [
        {"rate_of_return": 8}
      ],
      "session_memory": [],
      "output": {
        "function": "future_value_of_monthly_savings",
        "parameters": {
          "monthly_savings": 1000,
          "years": 20,
          "rate_of_return": 8
        },
        "need_more_info": False,
        "need_paramters": None
      }
    }

  ]
}
    
  ]}