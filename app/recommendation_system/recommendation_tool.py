from langchain_core.tools import StructuredTool
from langchain.tools import Tool
from langchain.vectorstores import FAISS
import asyncio
import faiss 
import os
from langchain_groq import ChatGroq
from recommendation_tool_prompts import manual_template,chatbot_template
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings
class AsyncMultiVectorRetriever():
    def __init__(self, retrievers):
        """Initialize with multiple retrievers (vector stores)."""
        self.retrievers = retrievers

    async def get_relevant_documents(self, query):
        """Fetch relevant documents from all vector stores."""
        docs = []
        tasks = [asyncio.to_thread(retriever.get_relevant_documents, query) for retriever in self.retrievers]
        try:
            results = await asyncio.gather(*tasks,return_exceptions=True)
            for result in results:
                if isinstance(result,Exception):
                    print(f"Error retrieving documents:{result}")
                else:
                    docs.extend(result)
        except Exception as e:
            print(f"An unexpected error occurred:{e}")
        return docs

def load_embeddings():
    try:
        embeddings=HuggingFaceEmbeddings()
        return embeddings
    except ModuleNotFoundError:
        print("Error: Required libraries (e.g., `sentence-transformers`) are missing. Install them using `pip install sentence-transformers`.")
    except OSError as e:
        print(f"OSError: Failed to load the embeddings model. Possible reasons: missing model, corrupted files, or network issues.\nDetails: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def initialise_chain(llm=None,policy_faiss_file,profile_faiss_file)->LLMChain:
    """
    Initializes and returns an LLM-based QA chain with FAISS-based retrieval.

    This function:
    - Loads embeddings.
    - Loads FAISS vector stores for policy and profile data asynchronously.
    - Initializes an asynchronous multi-vector retriever.
    - Sets up the chatbot prompt template.
    - Creates conversation memory for tracking interactions.
    - Instantiates and returns an LLM-based QA chain.

    Returns:
        LLMChain: A configured LLMChain instance for handling chatbot interactions.

    Raises:
        FileNotFoundError: If the FAISS index files are missing.
        ValueError: If there are invalid values in embeddings or retrievers.
        Exception: For any unexpected errors during initialization.
    """
    try:
        embeddings=load_embeddings()
        policy_vector_store=FAISS.load_local(policy_faiss_file,embeddings,allow_dangerous_deserialization=True)
        profile_vector_store=FAISS.load_local(profile_faiss_file,embeddings,allow_dangerous_deserialization=True)
        multi_retriever = AsyncMultiVectorRetriever(retrievers=[policy_vector_store, profile_vector_store])
        chatbot_prompt=PromptTemplate(input_variables=["context","history","question"],template=chatbot_template)
        memory = ConversationBufferMemory(memory_key="history", input_key="question", return_messages=True)
        qa_chain = LLMChain(llm=llm, prompt=chatbot_prompt, verbose=True)
        return qa_chain

    except FileNotFoundError:
        print("Error: FAISS index file not found. Please check the file path.")
    except ValueError as e:
        print(f"ValueError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


llm=ChatGroq(model_name="llama-3.3-70b-versatile")
def run_initialise_chain(llm):
    return asyncio.run(initialise_chain(llm,policy_faiss_index,profile_faiss_index))  # Ensures async function runs properly

# Define as a LangChain Tool
initialise_chain_tool = Tool(
    name="initialise_chain",
    func=run_initialise_chain,  # Calls the sync wrapper
    description="Initializes an LLM-based QA chain with FAISS retrieval."
)
