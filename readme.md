# ACS Pathway Pro: An LLM-Based QA System

## 1. Overview

**ACS Pathway Pro** is a specialized Question-Answering (QA) system designed to assist users with the **Australian Computer Society (ACS) General Skills Pathway** for migration. It leverages a **Retrieval-Augmented Generation (RAG)** pipeline combined with **intelligent Tool Calling** to provide accurate, grounded, and helpful responses.

The system is architected around an intelligent routing agent that handles user queries in two primary ways:

1. **Document-Based Answers (RAG):**
   For questions about established ACS policies, procedures, document requirements, or fees, the system uses a RAG pipeline to retrieve and synthesize answers directly from official ACS guideline documents.

2. **Email Inquiry Action (Tool Calling):**
   For questions that cannot be answered by the static documents—such as those about real-time application status, highly specific personal scenarios, or future policy changes—the system initiates a conversational workflow.
   It recognizes the query is outside its knowledge base, offers to forward the question to a human expert, and, upon user confirmation, uses a tool to send an email inquiry on their behalf.

This project fulfills the requirements for **KIT719 Project 2** by implementing a robust, prompt-driven routing logic that intelligently decides between retrieving information and performing a direct action — creating a highly specialized and useful assistant that directly incorporates assessor feedback.

---

## 2. System Architecture

The system follows a modular architecture orchestrated by a central, conversational agent.

* **Frontend:** A clean and user-friendly web interface built with **Gradio**.
* **Backend:** A Python application powered by the **Google Gemini Pro** model, which acts as the core reasoning engine.
* **Intelligent Routing Logic:** The system's behavior is governed by a detailed system prompt. This prompt instructs the agent to first analyze the user's query intent. Based on this analysis, it either calls the RAG tool for information retrieval or directly initiates the email inquiry workflow for out-of-scope questions.
  This avoids rigid, hard-coded rules and allows for flexible, context-aware routing.

For a detailed visual representation of the architecture and RAG pipeline, see **[Architecture Overview](architecture.md)**.

---

## 3. Setup and Running the Application

Follow these steps to run the application locally.

### **Prerequisites**

* Python 3.9+
* A Gmail account with **2-Step Verification** and an **App Password** enabled

---

### **Step 1: Clone the Repository**

```bash
git clone <your-repo-url>
cd acs-pathway-pro
```

---

### **Step 2: Create and Activate a Virtual Environment**

```bash
# For macOS / Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

---

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **Step 4: Configure Environment Variables**

Copy the example environment file and add your secret keys.

```bash
cp .env.example .env
```

Now, open the `.env` file and add your keys:

| Variable                | Description                                                                     |
| ----------------------- | ------------------------------------------------------------------------------- |
| `GOOGLE_API_KEY`        | Your API key from Google AI Studio.                                             |
| `SENDER_EMAIL`          | Your full Gmail address that will send the emails.                              |
| `SENDER_EMAIL_PASSWORD` | Your 16-digit **App Password** (not your normal password).                      |
| `RECIPIENT_EMAIL`       | The email address where inquiries will be received (e.g., your personal email). |

> ⚠️ **Note:** Ensure that 2-Step Verification is enabled in your Google account before creating the App Password.

---

### **Step 5: Add Grounding Documents**

Create a `documents` folder in the project root and place your **ACS General Skills Pathway PDF files** inside it.

---

### **Step 6: Run the Application**

Launch the Gradio application by running:

```bash
python main.py
```

The terminal will provide a local URL (e.g., `http://127.0.0.1:7860`). Open this link in your web browser to use the application.

---

## 4. Example Usage

### **Example 1: RAG-based Query**

```
User: What is a statutory declaration?
System: [Source 1 - ACS Guidelines]: A Statutory Declaration is a written statement declared to be true in the presence of an authorized witness. It may be required if you cannot provide sufficient evidence for your employment claims, such as lacking official payslips.
```

### **Example 2: Tool-based Email Inquiry**

```
User: What are the expected changes to the skilled occupation lists for the next financial year?
System: That's a great question about future updates, which I can't find in my current documents. If you'd like, I can send your question to the support team. What is your email address?
User: my email is test@example.com
System: Your inquiry has been successfully sent. The support team will reply to your email address shortly.
```

---

## 5. Design Choices & Logic

* **Intelligent Prompt-Driven Routing:** The core of the system is a detailed system prompt that instructs the LLM on how to act as an intelligent router. It defines the available tools (`acs_document_retriever`, `send_inquiry_email`) and provides criteria for the LLM to analyze the user's intent and decide whether to search the documents or immediately initiate the email inquiry. This is more sophisticated than a simple sequential check.

* **Action-Oriented Tool:** The `send_inquiry_email` tool was chosen over the initial generic web search to create a more specialized and in-scope assistant, directly addressing assessor feedback. The tool performs a direct action (sending an email) rather than just retrieving information, which demonstrates a more advanced and relevant use of tool calling.

* **Local Embeddings:** The system uses `all-MiniLM-L6-v2` via `HuggingFaceEmbeddings` to generate text embeddings locally. This avoids API rate limits and costs, making the application reliable and self-contained for academic and development purposes.

* **Modular Codebase:** The code is organized into separate files for configuration (`config.yml`), prompts (`prompt.py`), and main logic (`main.py`), adhering to software engineering best practices for clarity and maintainability.

---

## 6. Limitations & Failure Points

Based on testing, the following limitations were identified:

* **Conversational Memory for Inquiries:** The agent uses the conversation history to pass the original question to the email tool. In very long, complex conversations where the user's initial problem is discussed over several messages, the exact context might be lost when the email tool is finally called. A more advanced implementation would use a robust state management system to lock in the initial problem statement.

* **Hardcoded RAG Failure Signal:** The system's reliability was improved by using a specific signal (`DOCUMENT_SEARCH_FAILED`) to trigger the email flow. While robust, this is a form of hard-coded logic between a tool and the prompt. A more flexible approach might involve the LLM analyzing the semantic content of the RAG tool's output to determine if it was successful.

* **Lack of User Edit on Email:** The system automatically drafts and sends the email based on the user's initial query. It does not currently offer the user a chance to review or edit the email body before it is sent. This was a design choice for simplicity but could be a key area for future improvement.
