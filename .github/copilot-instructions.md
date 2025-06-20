# Copilot Instructions for Invoice Reimbursement System

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is an Invoice Reimbursement System project built with:
- **FastAPI** for API development
- **LangChain** for LLM integration and tool usage
- **Gemini** as the primary LLM for invoice analysis and chatbot
- **Qdrant** as the vector database for storing embeddings
- **Sentence-Transformers** for embedding generation
- **PDF processing** libraries for extracting text from documents

## Key Components:
1. **Invoice Analysis Endpoint**: Processes PDF invoices against HR policies using LLM
2. **RAG Chatbot Endpoint**: Provides intelligent querying of processed invoices
3. **Vector Store Integration**: Manages embeddings and metadata in Qdrant
4. **PDF Processing**: Handles policy and invoice document parsing

## Code Guidelines:
- Follow FastAPI best practices for endpoint design
- Use proper error handling and logging
- Implement comprehensive docstrings for all functions
- Use type hints throughout the codebase
- Follow the project structure for modular development
- Ensure secure handling of API keys and sensitive data
