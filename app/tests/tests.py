from Tools.REPLTool.repl_tool import Run_Python_Script
import asyncio

function = "cost_of_smoking"
args_dict = {
    "cigarettes_per_day" : 2,
    " cigarettes_per_pack" :10 ,
    "price_per_pack" : 200,
    "years_smoking" :1 ,
}

async def test_repl(func = function, args_dict = args_dict):
    result = await Run_Python_Script(func,args_dict)
    print(f"Finally got the result : {result}")
    
asyncio.run(test_repl())