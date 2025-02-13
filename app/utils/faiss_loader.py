import asyncio
import torch
import faiss
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from .logger import LOGGER
from .config import EMBEDDING_MODEL_NAME

# Global FAISS cache
FAISS_CACHE = {}
EMBEDDING_MODEL = None

async def load_embedding_model(name: str):
    """
    Loads the embedding model for FAISS on GPU if available.

    Returns:
        HuggingFaceEmbeddings: Embedding model.
    """
    global EMBEDDING_MODEL
    device = "cuda" if torch.cuda.is_available() else "cpu"
    LOGGER.info(f"Loading embedding model on {device}...")
    try :
        EMBEDDING_MODEL = HuggingFaceEmbeddings(
            model_name = name,
            model_kwargs={"device": device}  # Load model on GPU if available
        )
    except Exception as e:
        LOGGER.error(f"Failed to load embedding model: {str(e)}")
        raise 
    LOGGER.info("Model loaded successfully!")
    return  EMBEDDING_MODEL


async def load_faiss_retrievers(policy_faiss_file: str, profile_faiss_file: str, fandq_faiss_file : str ,embeddings = None, use_gpu: bool = False):
    """
    Loads FAISS indexes into memory (RAM) during startup and caches them.

    Args:
        policy_faiss_file (str): Path to FAISS index for policy.
        profile_faiss_file (str): Path to FAISS index for profile.
        embeddings: Embedding model for FAISS.
        use_gpu (bool): Whether to use GPU acceleration.

    Returns:
        dict: Cached FAISS retrievers.
    """
    global FAISS_CACHE
    
    if not embeddings and not EMBEDDING_MODEL:
        embeddings = await load_embedding_model(EMBEDDING_MODEL_NAME)
    
    
    if "policy" in FAISS_CACHE and "profile" in FAISS_CACHE and "fandq" in FAISS_CACHE:
        LOGGER.info("FAISS indexes already loaded.")
        return FAISS_CACHE  # Return cached indexes if already loaded

    LOGGER.info("Loading FAISS indexes...")

    policy_vector_store = FAISS.load_local(
        policy_faiss_file, embeddings, allow_dangerous_deserialization=True
    )  # Correct placement of the parameter
    profile_vector_store = FAISS.load_local(
        profile_faiss_file, embeddings, allow_dangerous_deserialization=True
    )  # Correct placement of the parameter
    fandq_vector_store = FAISS.load_local(
        fandq_faiss_file, embeddings, allow_dangerous_deserialization=True
    )  # Correct placement of the parameter

    # Move FAISS index to GPU if enabled
    if use_gpu and torch.cuda.is_available():
        LOGGER.info("Moving FAISS indexes to GPU...")
        policy_vector_store.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, policy_vector_store.index)
        profile_vector_store.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, profile_vector_store.index)
        fandq_vector_store.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, fandq_vector_store.index)
    else:
        LOGGER.info("Using FAISS on CPU.")

    # Store in global cache
    FAISS_CACHE["policy"] = policy_vector_store
    print(f"The type faiss retriever : {policy_vector_store} ")
    FAISS_CACHE["profile"] = profile_vector_store
    FAISS_CACHE["fandq"] = fandq_vector_store
    return FAISS_CACHE



