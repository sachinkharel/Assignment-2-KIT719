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
import yagmail


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

retriever = vector_store.as_retriever(search_kwargs={"k": 6})

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
            return "DOCUMENT_SEARCH_FAILED"
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
def send_inquiry_email(original_question: str, user_email: str) -> str:
    """
    Use this tool AFTER you have asked for and received the user's email address.
    This tool drafts AND SENDS an email to the support team.
    """
    print(f"--- INFO: Calling 'send_inquiry_email' tool for: '{original_question}' ---")
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")

        subject = f"Inquiry from ACS Pathway Pro: {original_question[:50]}..."
        body = (
            f"Reply to: {user_email}\n\n"
            f"A user asked the following question that could not be answered by the documentation:\n\n'{original_question}'"
        )

        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(to=recipient_email, subject=subject, contents=body)
        print("--- INFO: Email sent successfully! ---")
        return "Your inquiry has been successfully sent. The support team will reply to your email address shortly."
    except Exception as e:
        logging.exception("Email sending failed")
        return f"Sorry, there was a critical error sending your email: {e}"

# --- Initialize Gemini model ---
model = genai.GenerativeModel(
    model_name=cfg.get("model_name"),
    system_instruction=SYSTEM_PROMPT,
    tools=[acs_document_retriever.func, send_inquiry_email.func],
)

chat = model.start_chat(enable_automatic_function_calling=True)

# --- Gradio UI ---

def get_chatbot_response(user_query, chat_history):
    """
    Handles the chat interaction by sending the user's message to the
    ongoing chat session and returning the bot's reply.
    """
    chat_history = chat_history or []
    try:
        # This single line handles the entire conversation, including all tool calls.
        response = chat.send_message(user_query)
        reply = response.text
    except Exception as e:
        logging.exception("Chat send_message failed")
        reply = f"An error occurred: {e}"
    
    chat_history.append((user_query, reply))
    
    # Return an empty string to clear the textbox, and the updated chat history.
    return "", chat_history


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # ACS Skill Assessment Assistant
        ### Your expert guide for the General Skills Pathway.
        """
    )
    
    chatbot_ui = gr.Chatbot(label="ACS Pathway Pro", height=500, bubble_full_width=False)
    
    with gr.Row():
        msg_textbox = gr.Textbox(
            label="Your Question",
            placeholder="Ask a question about the ACS assessment...",
            lines=1,
            scale=4
        )
        submit_button = gr.Button("Send", variant="primary", scale=1)
    
    clear_button = gr.ClearButton([msg_textbox, chatbot_ui])

    # Wire up the components directly to the main response function.
    msg_textbox.submit(
        get_chatbot_response, 
        [msg_textbox, chatbot_ui], 
        [msg_textbox, chatbot_ui]
    )
    submit_button.click(
        get_chatbot_response, 
        [msg_textbox, chatbot_ui],
        [msg_textbox, chatbot_ui]
    )

if __name__ == "__main__":
    demo.launch(share=False, debug=True)