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
            # Run similarity_search in a separate thread (since FAISS is not async)
            docs = await asyncio.to_thread(self.vector_store.similarity_search, query, k=4)
            LOGGER.info(f"Retrieved {len(docs)} documents.")  # ✅ Log the result count
            return docs if docs else []
        except Exception as e: 
            LOGGER.error(f"An error occurred: {e}\n{traceback.format_exc()}")  # ✅ Print full traceback
            return []

async def get_policy_recommendation(query,FAISS_CACHE = FAISS_CACHE):
    """
    Fetch policy and profile recommendations asynchronously.
    
    Args:
        query (str): The search query.
    
    Returns:
        list: A combined list of relevant documents from both vector stores.
    """
    policy_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["policy"])
    profile_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["profile"])
    LOGGER.info("Initialised Policy and Profile RAG")
    policy_docs, profile_docs = await asyncio.gather(
        policy_retriever.get_relevant_documents(query),
        profile_retriever.get_relevant_documents(query)
    )
    LOGGER.info("Got resutls for Policy and Profile RAG")
    return (policy_docs, profile_docs ) # Merge results

async def get_fandqs(query, FAISS_CACHE = FAISS_CACHE):
    """
    Fetch FAQs asynchronously based on the query.

    Args:
        query (str): The search query.

    Returns:
        list: A list of relevant FAQ documents.
        
    """
    LOGGER.info("Getting documents from the FAQ RAG...")
    try:
        fandq_retriever = AsyncMultiVectorRetriever(FAISS_CACHE["fandq"])
        LOGGER.info("Initalised fandq RAG.")
    except Exception as e:
        LOGGER.error(f"There was some while loading the FAQ RAG. : {e}")
    return await fandq_retriever.get_relevant_documents(query)