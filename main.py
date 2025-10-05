# main.py
import os
import logging
from dotenv import load_dotenv
import yaml

# UI
import gradio as gr

# Google Generative AI
import google.generativeai as genai

# LangChain & helpers
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.tools import tool

# load system prompt
from prompt import SYSTEM_PROMPT

# load config
with open("config.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# load env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY in your .env (see .env.example)")

# configure google sdk
genai.configure(api_key=GOOGLE_API_KEY)

# --- Document loading & splitting ---
doc_path = cfg.get("docs_path")
if not os.path.exists(doc_path):
    logging.warning("Document folder '%s' does not exist. Create it and add PDFs.", doc_path)

pdf_files = [f for f in os.listdir(doc_path) if f.lower().endswith(".pdf")] if os.path.isdir(doc_path) else []
all_docs = []
for pdf in pdf_files:
    loader = PyPDFLoader(os.path.join(doc_path, pdf))
    pages = loader.load()
    all_docs.extend(pages)

print(f"Loaded {len(all_docs)} pages from {len(pdf_files)} PDF files.")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=cfg.get("chunk_size"),
    chunk_overlap=cfg.get("chunk_overlap")
)
chunked_docs = text_splitter.split_documents(all_docs)
print(f"Split {len(all_docs)} pages into {len(chunked_docs)} chunks.")

# --- Embeddings & vector store (local HuggingFace) ---
if cfg.get("use_local_embeddings"):
    embedding_model = HuggingFaceEmbeddings(model_name=cfg.get("embedding_model"))
else:
    raise NotImplementedError("Only local embeddings are implemented in this template.")

vector_store = Chroma.from_documents(
    documents=chunked_docs,
    embedding=embedding_model,
    persist_directory=cfg.get("chroma_persist_directory")
)

retriever = vector_store.as_retriever()

# --- Tools ---
@tool
def acs_document_retriever(query: str) -> str:
    """
    Searches the local ACS documents vector store for relevant content.
    Use this for ACS-specific policy / documents / application process queries.
    """
    print(f"--- INFO: Calling RAG Retriever for query: '{query}' ---")
    try:
        # prefer standard LangChain API
        docs = retriever.invoke(query)
        if not docs:
            return "No documents found matching your query in the ACS corpus."
        else:
            response_parts = []
            for i, doc in enumerate(docs, start=1):
                content = doc.page_content
                response_parts.append(f"[Source {i} - ACS Guidelines]: {content}")
            return "\n\n".join(response_parts)
    except Exception as e:
        logging.exception("acs_document_retriever failed")
        return f"Error retrieving ACS documents: {e}"

@tool
def web_search(query: str) -> str:
    """
    Performs a web search for questions outside the ACS docs (salaries, job market, visa updates).
    If duckduckgo dependencies are missing this will return an informative message.
    """
    print(f"--- INFO: Calling Web Search for query: '{query}' ---")
    try:
        # import here to allow graceful fallback if ddgs isn't installed
        from langchain_community.tools import DuckDuckGoSearchRun
        search_tool = DuckDuckGoSearchRun()
        return search_tool.run(query)
    except ImportError as ie:
        logging.exception("ddgs missing for DuckDuckGoSearchRun")
        return "Web search is unavailable because 'ddgs' is not installed. Install it with `pip install -U ddgs`."
    except Exception as e:
        logging.exception("web_search failed")
        return f"Web search failed: {e}"

# --- Initialize Gemini model (pass raw callables) ---
model = genai.GenerativeModel(
    model_name=cfg.get("model_name"),
    system_instruction=SYSTEM_PROMPT,
    tools=[acs_document_retriever.func, web_search.func],
)

chat = model.start_chat(enable_automatic_function_calling=True)

# --- Gradio UI ---
def get_chatbot_response(user_query, chat_history):
    """
    Handles user input and returns structured messages for Chatbot(type='messages').
    """
    chat_history = chat_history or []
    try:
        response = chat.send_message(user_query)
        reply = response.text
    except Exception as e:
        logging.exception("Chat send_message failed")
        reply = f"Model call failed: {e}"

    # Append messages in the correct format
    chat_history.append({"role": "user", "content": user_query})
    chat_history.append({"role": "assistant", "content": reply})

    return "", chat_history

def build_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # ACS Skill Assessment Assistant
            **ACS Pathway Pro** — ask about the ACS General Skills Pathway or related job-market questions.
            """
        )
        chatbot_ui = gr.Chatbot(label="ACS Pathway Pro", height=500, type='messages')
        msg_textbox = gr.Textbox(label="Your Question", placeholder="e.g., What documents do I need for proof of identity?")
        msg_textbox.submit(get_chatbot_response, [msg_textbox, chatbot_ui], [msg_textbox, chatbot_ui])
        gr.ClearButton([msg_textbox, chatbot_ui])
    return demo

if __name__ == "__main__":
    demo = build_ui()
    # For local development: share=False. Set share=True in Colab if you need a public link
    demo.launch(share=False, debug=True)
