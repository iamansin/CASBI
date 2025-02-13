import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from Utils.logger import LOGGER
from textwrap import dedent
from langchain_experimental.tools import PythonREPLTool

REPL_CODE_ENV = PythonREPLTool()

CODE = dedent("""

from typing import Union

def future_cost_planner(current_cost: float, years: int, inflation_rate: float) -> float:
    
    # Calculates the future cost of an item based on inflation.

    # Parameters:
    #     current_cost (float): The current price of the item.
    #     years (int): Number of years in the future.
    #     inflation_rate (float): Annual inflation rate in percentage.
    # Returns:
    #     float: Future cost of the item.
    
    print(current_cost * ((1 + inflation_rate / 100) ** years))


def cost_of_smoking(
    cigarettes_per_day: int, cigarettes_per_pack: int, price_per_pack: float, years_smoking: int = 1
) -> float:
    
    # Computes the total cost of smoking over a period.

    # Parameters:
    #     cigarettes_per_day (int): Number of cigarettes smoked per day.
    #     cigarettes_per_pack (int): Number of cigarettes in a pack.
    #     price_per_pack (float): Price of one pack of cigarettes.
    #     years_smoking (int, optional): Duration of smoking in years (default is 1).

    # Returns:
    #     float: Total cost of smoking over the given years.

    cost_per_cigarette = price_per_pack / cigarettes_per_pack
    print(cigarettes_per_day * cost_per_cigarette * 365 * years_smoking)


def future_value_of_monthly_savings(monthly_savings: float, years: int, rate_of_return: float) -> float:

    # Calculates the future value of savings with a given rate of return.

    # Parameters:
    #     monthly_savings (float): Amount saved per month.
    #     years (int): Number of years saving.
    #     rate_of_return (float): Annual return rate in percentage (capped at 50%).

    # Returns:
    #     float: Future value of savings.

    rate_of_return = min(rate_of_return, 50)  # Cap at 50% to avoid unrealistic values
    monthly_rate = (rate_of_return / 100) / 12
    months = years * 12
    future_value = monthly_savings * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    print(round(future_value, 2))


def time_to_double_money(amount: float, interest_rate: float) -> Union[str, tuple[int, int]]:

    # Estimates the time required to double an investment using the Rule of 72.

    # Parameters:
    #     amount (float): Initial amount of money.
    #     interest_rate (float): Annual interest rate in percentage.

    # Returns:
    #     Union[str, tuple[int, int]]: Time in years and months to double the money, 
    #     or an error message if the interest rate is invalid.

    if interest_rate <= 0:
        return "Interest rate must be greater than 0"

    years = int(72 / interest_rate)  # Rule of 72 formula
    remaining_months = round((72 / interest_rate - years) * 12)  # Get remaining months
    print(years, remaining_months)
""")

async def exe_function(function:str)-> str:
    await REPL_CODE_ENV.arun(CODE)
    result = await REPL_CODE_ENV.arun(function)
    if "Error" in result :
        raise ValueError(f"Not able to run the Script due to ->{ result }") 
    return result

#This is the main function which runs the scripts.
async def Run_Python_Script(function : str ,args_dict : dict) -> str:
    """This function is basically a tool that help in running python Scripts.
    
    Args : Takes arguments that should be passed to functions 
        args_dict : str = This is a dict of arguments as key and their values.
    
    Returns : This function returns a result after running the Scripts.
    """
    args_str = ", ".join(f"{key}={value}" for key, value in args_dict.items())
    fun_exe_call = f"{function}({args_str})"
    try:
        result = await exe_function(fun_exe_call)
        return result
    except ValueError as e:
        LOGGER.error(e)
        
    return "Not able to process request"
        
        
    
    
    
    
    
        
    
    
