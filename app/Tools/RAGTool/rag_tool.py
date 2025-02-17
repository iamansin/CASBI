import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
import traceback
import os
from Utils.faiss_loader import  FAISS_CACHE
from Utils.logger import LOGGER

class AsyncMultiVectorRetriever():
    def __init__(self, vector_store):
        """Initialize with multiple retrievers (vector stores)."""
        self.vector_store = vector_store

    async def get_relevant_documents(self, query):
        """Fetch relevant documents from the vector store."""
        LOGGER.info("Asynchronously getting the response from similarity_search:")
        try:
            docs = await self.vector_store.asimilarity_search(query, k=4)
            LOGGER.info(f"Retrieved {len(docs)} documents.")  # ✅ Log the result count
            return docs if docs else []
        except Exception as e: 
            LOGGER.error(f"An error occurred: {e}\n{traceback.format_exc()}")
            return []


async def get_policy_recommendation(query,FAISS_CACHE = FAISS_CACHE):
    """
    Fetch policy and profile recommendations asynchronously.
    
    Args:
        query (str): The search query.
    
    Returns:
        list: A combined list of relevant documents from both vector stores.
    """

    policy_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["Policy"])
    profile_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["Profile"])
    LOGGER.info("Initialised Policy and Profile RAG")
    policy_docs = await policy_retriever.get_relevant_documents(query)
    policy_docs, profile_docs = await asyncio.gather(
        policy_retriever.get_relevant_documents(query),
        profile_retriever.get_relevant_documents(query)
    )
    LOGGER.info("Got resutls for Policy and Profile RAG")
    return policy_docs , profile_docs

async def get_fandqs(query,FAISS_CACHE = FAISS_CACHE):
    """
    Fetch FAQs asynchronously based on the query.

    Args:
        query (str): The search query.

    Returns:
        list: A list of relevant FAQ documents.
        
    """
    LOGGER.info("Getting documents from the FAQ RAG...")
    try:

        fandq_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["Fandq"])
        LOGGER.info("Initalised fandq RAG.")
    except Exception as e:
        LOGGER.error(f"There was some while loading the FAQ RAG. : {e}")
    return await fandq_retriever.get_relevant_documents(query)

async def get_services(query, FAISS_CACHE = FAISS_CACHE):
    """
    Fetch Services asynchronously based on the query.

    Args:
        query (str): The search query.

    Returns:
        list: A list of relevant Service documents.
        
    """
    LOGGER.info("Initialising Serveices retriever..")
    try:
        services_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["Services"])
        LOGGER.info("Initialised Services RAG")
    except Exception as e:
        LOGGER.error(f"There was some while loading the Services RAG. : {e}")
    
    return await services_retriever.get_relevant_documents(query)
    