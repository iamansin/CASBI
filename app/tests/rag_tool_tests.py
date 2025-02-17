import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.Utils.logger import LOGGER
from app.Utils.faiss_loader import load_faiss_retrievers
from app.Tools.RAGTool.rag_tool import get_fandqs, get_policy_recommendation, get_services
import asyncio

async def model_loading_test(query_for_fandq:str|None = None, query_for_policy : str | None = None, query_for_services : str | None = None):
    print("loading faiss ..." )
    model_load_time = time.time()
    faiss_cache = await load_faiss_retrievers(
            policy_faiss_file="./app/faiss_indexes/policy_faiss_final_index",
            profile_faiss_file="./app/faiss_indexes/profile_faiss_final_index",
            fandq_faiss_file="./app/faiss_indexes/fandq_faiss_index",
            services_faiss_file="./app/faiss_indexes/services_faiss_index",
            use_gpu=True  # Set False for CPU
        )
    print(f"Time taken to load the model and faiss index to the gpu {time.time()-model_load_time}")
    print("running the rag tool ....")
    try :
        if query_for_fandq :
            faq_time = time.time()
            print("running the fandqs function:")
            rag_result = await get_fandqs(query_for_fandq, faiss_cache)
            print(f"Time taken to get the documents from the faq : {time.time()-faq_time}")
            print(f"results of the the RAG TOOL : { rag_result}")
            print("*" * 80)
        if query_for_policy :
            print("now running the policy tool")
            policy_time = time.time()
            policy_result, profile= await get_policy_recommendation(query_for_policy,faiss_cache)
            print(f"The time taken to get policy results : {time.time()-policy_time}")
            print(f"Got results from the policy tool : {policy_result}")
            print("*" * 80)
            print(f"Got results for Profile : {profile} ")
            print("*" * 80)
        if query_for_services:
            service_time = time.time()
            services_result = await get_services(query_for_services,faiss_cache)
            print(f"Time taken to get results for services : {time.time()-service_time}")
            print(f"Got results for services : {services_result}")
            print("*" * 80)
        return print("working fine!")
    except Exception as e:
        print(f"There was some proble while running test : {e}")
        
        
    
query_for_policy = "My age is 22 i am married and one kid who is 5 years old.Can you please provide me with some good policies?"
query_for_fandq = "how to change my address"
query_for_services = "I want to pay my premium online"
asyncio.run(model_loading_test(query_for_fandq=query_for_fandq, query_for_policy=query_for_policy, query_for_services=query_for_services))
    