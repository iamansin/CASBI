from typing_extensions import List, TypedDict, Dict, Any, Literal
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    message : HumanMessage
    selected_tools : List[List[str]] 
    primary_objective : str
    user_long_term_memory : str
    user_short_term_memory : str   
    final_response : str
    tool_redirect : bool
    tool_results : Dict
    next_node : str
    thought : str
    last_tool_results : List[str]
    prompt : str 
    tool_query : str
    existing_user : bool
    
class Initial_Output_Structure(BaseModel):
    """
    Defines the execution strategy for handling user queries by selecting and sequencing tools.
    """
    selected_tools: List[
        Literal['fandq_tool', 'service_tool', 'recommendation_tool', 'calculator_tool', 'payment_tool','final_tool']
    ] = Field(
        description="Tools required to solve the query with their execution order. Tools with the same step number will be executed in parallel.\n"
                    "\n🔹 **service_tool** → Use only for user complaints or requests that need human customer care assistance."
                    "\n🔹 **recommendation_tool** → Use only if the user expresses interest in policy recommendations."
                    "\n🔹 **fandq_tool(Frequently Asked Questions Database)** → Use only if the user’s question closely matches FAQs. Do not use for casual greetings."
                    "\n🔹 **calculator_tool** → Use only when there is a need to a calculate something or if the user specifically asks for some calculations."
                    "\n🔹 **payment_tool** → Use only when there is a request for a payment after user has asked for policy recommendation."
                    "\n🔹 **final_tool** → Use this as default for simple responses (e.g., greetings, acknowledgments, confirmations)."
    )

    primary_objective: str = Field(description="Clear outcome-focused goal statement")
    
    class Config:
        json_schema_extra = {
  "examples": [
    {
      "selected_tools": ["service_tool"],
      "primary_objective": "Guide the user through the initial steps of filing a claim and connect them with an agent.",
    },
    {
      "selected_tools": ["recommendation_tool"],
      "primary_objective": "Guide the user through life insurance options and answer their questions.",
    },
    {
      "selected_tools": ["final_tool"],
      "primary_objective": "Acknowledge the user's greeting with a friendly response.",
    },
    {
      "selected_tools": ["final_tool"],
      "primary_objective": "Provide a direct answer without using any tool, as user is only saying hi/hello.",
    },
    {
      "selected_tools": ["calculator_tool"],
      "primary_objective": "Calculate and explain the impact of smoking on insurance premiums.",
    }
    # {
    #   "understanding": "User wants to know the status of their submitted application.",
    #   "selected_tools": {
    #     "step_1": "fandq_tool",
    #     "step_2": "service_tool",
    #     "step_3": "final_tool"
    #   },
    #   "primary_objective": "Provide application status information and offer support through a customer care agent.",
    #   "execution_sequence": [
    #     "1. Answer FAQs about application status and processing times.",
    #     "2. If the user has specific questions, connect them with a customer care agent.",
    #     "3. End the conversation."
    #   ]
    # },
    # {
    #   "understanding": "User is interested in learning about investment options related to their insurance policy.",
    #   "selected_tools": {
    #     "step_1": "recommendation_tool",
    #     "step_2": "fandq_tool",
    #     "step_3": "final_tool"
    #   },
    #   "primary_objective": "Educate the user on investment-linked insurance policies.",
    #   "execution_sequence": [
    #     "1. Recommend relevant insurance policies with investment options.",
    #     "2. Answer user questions about the investment options using FAQs.",
    #     "3. End the conversation."
    #   ]
    # },
    
  ]
}
class Thinker_Output_Structure(BaseModel):
  selected_tools : List[str] = Field(description="This field contains the list of tools that has to be executed.")
  
class Final_Output_Structure(BaseModel):
    response : str =Field(description="This field contains final results.")
    
class Memory_Structured_Output(BaseModel):
    long_term_memory : str | None = Field(description="This field contains the long term memory that has been extracted from the session converstation.")

class Final_Tool_Structure(BaseModel):
  think_more : bool = Field(description="This field is a boolean value, if there is more information required to proceed further then True else if current inforamtion is sufficient then False.")
  thought : str | None = Field(description="This field contains the thought that the Thinker node will use to get more clear instructions on procceding further. If Current information is sufficient then this field will be None.")
  response : str | None = Field(description="This field contains the response that has to be sent to the user. If there is no response then this field will be None.")
  
class Observer_Output_Structure(BaseModel):
  prompt : str = Field(description= "This field contains the prompt that has to passed to other node to generate/ think of using next step or tool to use.")
  next_node : Literal["final_node", "thinker_node"] = Field(description= "This fiel contains the name of next node to be selected.")
  tool_query : str|None = Field(description= "This field contains enhanced query for the tool. If tool to use this field contains a str else None")

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
class Payment_Tool_Structure(BaseModel):
  selected_policies:str=Field(description="This gives existing policies the user holds and their status along with newly selected policies if any. The policies should be "
  "displayed in this format:"
  "policy_name:status"
  "The status can be:accepted, declined, modified,to be payed")
  payment_url:str=Field(description="This is to provide a payment url of the form:https://www.samplepaymenturl.com")
  