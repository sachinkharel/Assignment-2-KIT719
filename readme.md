# ACS Pathway Pro: An LLM-Based QA System

## 1. Overview

ACS Pathway Pro is a Question-Answering (QA) system designed to assist users with the Australian Computer Society (ACS) General Skills Pathway for migration. It leverages a Retrieval-Augmented Generation (RAG) pipeline combined with Tool Calling to provide accurate, grounded answers.

The system is built to answer two main types of queries:
1.  **Document-Specific Questions:** Using a RAG pipeline over official ACS guideline documents to answer questions about the application process, required documents, fees, and skill requirements.
2.  **External Knowledge Questions:** Using a web search tool to answer questions about topics not covered in the documents, such as current salary trends, job market data, and live visa processing updates.

This project fulfills the requirements for KIT719 Project 2 by implementing a robust, prompt-driven routing logic to seamlessly switch between its internal knowledge base and external tools.

## 2. System Architecture

The system follows a modular architecture orchestrated by a central agent.

-   **Frontend:** A clean and user-friendly web interface built with Gradio.
-   **Backend:** A Python application powered by the Google Gemini Pro model.
-   **Routing Logic:** A prompt-driven agent decides whether to use the RAG pipeline or a web search tool based on the user's query. This avoids hard-coded rules and allows for flexible, context-aware responses.

For a detailed visual representation of the architecture and RAG pipeline, please see the **[Architecture Overview](architecture.md)**.

## 3. Setup and Running the Application

Follow these steps to run the application locally.

**Prerequisites:**
*   Python 3.9+
*   Access to a terminal or command prompt

**Step 1: Clone the Repository**

git clone <repo-url>

cd acs-pathway-pro

**Step 2: Create and Activate a Virtual Environment**

**For macOS / Linux**

python3 -m venv venv
source venv/bin/activate

**For Windows**

python -m venv venv
.\venv\Scripts\activate

**Step 3: Install Dependencies**
Install all required packages from the requirements.txt file.
pip install -r requirements.txt

**Step 4: Configure Environment Variables**
Copy the example environment file and add your Google AI API key.
cp .env.example .env

**Now, open the .env file and add your key:**

**GOOGLE_API_KEY=your_google_api_key_here**

**Step 5: Add Grounding Documents**
Create a documents folder in the project root and place your ACS General Skills Pathway PDF files inside it.

**Step 6: Run the Application**
Launch the Gradio application by running main.py.
python main.py
The terminal will provide a local URL (e.g., `http://127.0.0.1:7860`). Open this link in your web browser to use the application.

## 4. Example Usage

**Example 1: RAG-based Query**
> **User:** What is a statutory declaration?
>
> **System:** According to the ACS guidelines, a Statutory Declaration is a written statement declared to be true in the presence of an authorized witness. It may be required if you cannot provide sufficient evidence for your employment claims, such as lacking official payslips.

**Example 2: Tool-based Query**
> **User:** What is the average salary for a developer programmer in Australia?
>
> **System:** Based on a web search, the average salary for a Developer Programmer in Australia is between AUD $90,000 and $110,000 per year, depending on experience and location.

## 5. Design Choices & Logic

-   **Prompt-Driven Routing:** The core of the system is a detailed system prompt that instructs the LLM on how to act as a router. It defines the available tools (`acs_document_retriever`, `web_search`) and provides clear criteria for when to use each. This is more flexible and robust than hard-coded `if/else` logic.
-   **Local Embeddings:** The system uses `all-MiniLM-L6-v2` via `HuggingFaceEmbeddings` to generate text embeddings locally. This avoids API rate limits and costs associated with cloud-based embedding services, making the application more reliable and self-contained.
-   **Modular Codebase:** The code is organized into separate files for configuration (`config.yml`), prompts (`prompts.py`), and main logic (`main.py`), adhering to software engineering best practices.

## 6. Limitations & Failure Points

Based on testing with difficult queries, the following limitations were identified:

1.  **Ambiguity Handling:** For vague queries like "tell me about the assessment," the system defaults to its primary RAG tool rather than asking for user clarification. This can sometimes lead to answers that are correct but not what the user intended.
2.  **Complex Multi-step Reasoning:** The system is designed to select one tool per turn. For a query like "What is the fee in AUD and can you convert it to USD?", it will correctly answer the first part but will not automatically perform the second (conversion) step. This would require a more complex agentic framework.
3.  **Knowledge Cutoff:** The RAG pipeline is limited to the information present in the uploaded PDFs. If the documents are out of date, the system will provide outdated information. This is mitigated by the web search tool, but the model may not always know that its document knowledge is stale.
