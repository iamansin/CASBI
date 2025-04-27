# 📌 AI Chat Agent for SBI Life Insurance Hackathon  

## 🌟 Overview  
Our AI-powered **WhatsApp Chat Agent** is designed to **revolutionize customer interactions** for SBI Life Insurance. Built using **LangGraph**, this intelligent assistant seamlessly integrates multiple tools to provide **instant, accurate, and personalized support** to users.  

## 🚀 Key Features & Capabilities  
- **Conversational AI on WhatsApp** – Enables natural, real-time interaction with users.  
- **Multi-Tool Functionality** – Equipped with specialized tools to handle a variety of queries and services.  
- **Personalized Assistance** – Remembers user preferences and history for a more engaging experience.  
- **Lightning-Fast Responses** – Processes text, images, and documents with minimal latency.  

## 🛠 Integrated Tools & Functionalities  
- ✅ **FAQs Tool** – Provides instant answers to frequently asked questions about SBI Life Insurance policies and services.  
- ✅ **Services Tool** – Guides users through different insurance services, policy details, and offerings.  
- ✅ **Recommendation Tool** – Suggests the best insurance plans based on user inputs and requirements.  
- ✅ **Calculator Tool** – Helps users calculate premiums, coverage, and benefits in real-time.  
- ✅ **Payment Tool** – Facilitates secure and hassle-free premium payments directly through WhatsApp.  
- ✅ **Document Processing** – Allows users to share images and documents for policy verification and support.  

## 🎯 Why This Solution?  
- **Brings SBI Life's website services to WhatsApp** – Making insurance management easier than ever.  
- **Reduces dependency on customer support agents** – AI handles routine queries efficiently.  
- **Enhances accessibility** – No need for additional apps; users interact through a familiar platform.  
- **Streamlined user experience** – A single interface for all insurance-related needs.  

## 🔥 Impact & Future Scope  
This AI Chat Agent aims to **bridge the gap between digital insurance services and daily user needs**, ensuring **seamless, efficient, and intelligent assistance** for SBI Life customers. Future enhancements could include **voice interactions, multilingual support, and deeper policy analytics** to further enrich the user experience. 
The Structure of this Agent is Like :


![CASBI-AGENT](https://github.com/user-attachments/assets/bf3b14ec-4328-4bb0-994a-2cfcfa87b99f)


# File Structure Description

## 📂 app/ *(Main code folder)*
- **Agent/** *(Main Agent folder)*
  - `agent_state.py` *(Contains states and Pydantic models)*
  - `whatsapp_agent.py` *(Code for the WhatsApp ChatAgent)*

- **Tools/** *(Folder containing all tools)*
  - **PAYTool/** *(Tool for payment processing)*
    - `paytool.py`
  - **RAGTool/** *(RAG-based tool for FAQs, Services & Recommendations)*
    - `rag_tool.py`
  - **REPLTool/** *(Calculator tool that allows Agent to execute Python scripts dynamically)*
    - `repl_tool.py`
  - **UMTool/** *(User management tool for fetching user details)*
    - `user_manager.py`

- **faiss_indexes/** *(Contains all FAISS Indexes used)*
  - `fandq_faiss_index`
  - `policy_faiss_index`
  - `services_faiss_index`

- **utils/** *(Utility functions)*
  - `config.py` *(Imports environment variables)*
  - `connection_testing.py` *(Tests DB connections on startup)*
  - `faiss_loader.py` *(Loads FAISS index on GPU)*
  - `input_processor.py` *(Processes multi-modal input)*
  - `logger.py` *(Handles application logging)*
  - `memory_handler.py` *(Manages Agent memory)*
  - `message_handler.py` *(Sends messages to users)*
  - `prompts.py` *(Stores all application prompts)*

- `main.py` *(Runs the FastAPI server)*
- `webhook.py` *(Receives & processes messages)*

## 📂 logs/ *(Contains logs)*
- `application_logs.log`

## 📄 Other Files:
- `req.txt` *(Lists all required dependencies)*
