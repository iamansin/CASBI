import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.Utils.logger import LOGGER
from app.Utils.faiss_loader import load_faiss_retrievers
from app.Tools.RAGTool.rag_tool import get_fandqs, get_policy_recommendation
import asyncio

async def model_loading_test(query_for_fandq:str|None = None, query_for_policy : str | None = None):
    print("loading faiss ..." )
    faiss_cache,embeddings = await load_faiss_retrievers(
            policy_faiss_file="./app/faiss_indexes/policy_faiss_index",
            profile_faiss_file="./app/faiss_indexes/profile_faiss_index",
            fandq_faiss_file="./app/faiss_indexes/fandq_faiss_index",
            services_faiss_file="None",
            use_gpu=True  # Set False for CPU
        )
    print("running the rag tool ....")
    try :
        if query_for_fandq :
            print("running the fandqs function:")
            rag_result = await get_fandqs(query_for_fandq, faiss_cache)
            print(f"results of the the RAG TOOL : { rag_result}")
        if query_for_policy :
            print("now running the policy tool")
            policy_result = await get_policy_recommendation(query_for_policy,faiss_cache)
            print(f"Got results from the policy tool : {policy_result}")
        return print("working fine!")
    except Exception as e:
        print(f"There was some proble while running test : {e}")
        
        
    
query_for_policy = "My age is 22 i am married and one kid who is 5 years old.Can you please provide me with some good policies?"
query_for_fandq = "how to change my address"
asyncio.run(model_loading_test(query_for_fandq=query_for_fandq, query_for_policy=None))
    