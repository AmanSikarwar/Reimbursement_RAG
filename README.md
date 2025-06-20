# Invoice Reimbursement System

An intelligent invoice reimbursement analysis system built with FastAPI, LangChain, and vector databases. This system automates the process of analyzing employee invoice reimbursements against company policies using Large Language Models (LLMs) and provides a RAG-based chatbot for querying processed invoices.

## 🚀 Features

### Core Functionality

- **Automated Invoice Analysis**: Process PDF invoices against HR reimbursement policies using Gemini LLM
- **Intelligent Policy Compliance**: Determine reimbursement status (Fully Reimbursed, Partially Reimbursed, or Declined)
- **Vector Database Storage**: Store analysis results with embeddings in Qdrant for efficient retrieval
- **RAG-Powered Chatbot**: Natural language querying of processed invoice data
- **Batch Processing**: Handle multiple invoices via ZIP file uploads
- **Comprehensive Logging**: Detailed logging and error handling

### API Endpoints

1. **Invoice Analysis Endpoint** (`/api/v1/analyze-invoices`)

   - Upload HR policy PDF and invoice ZIP files
   - Automated analysis using Gemini LLM
   - Store results in vector database
2. **RAG Chatbot Endpoint** (`/api/v1/chat`)

   - Natural language queries about processed invoices
   - Context-aware responses with conversation history
   - Source document citations
   - **Smart Query Suggestions**: Get related query suggestions for better data exploration

## 🏗️ Architecture

### Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **LLM Integration**: LangChain + Google Gemini
- **Vector Database**: Qdrant
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF2
- **Configuration**: Pydantic Settings

### System Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │◄──►│   LLM Service   │◄──►│  Gemini API     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Vector Store    │◄──►│ PDF Processor   │◄──►│ File Utils      │
│ (Qdrant)        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Chatbot Service │
│ (RAG)           │
└─────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Qdrant server (local or cloud)
- Google Gemini API key

### Step 1: Clone and Setup

```bash
# Clone the repository (if using git)
git clone <repository-url>
cd Reimbursement_RAG

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configurations
```

Required environment variables:

```bash
# Gemini API Configuration
GOOGLE_API_KEY=your_gemini_api_key_here

# Qdrant Configuration (adjust as needed)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key_here  # Optional for cloud instances

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
```

### Step 3: Setup Qdrant

```bash
# Option 1: Run Qdrant with Docker
docker run -p 6333:6333 qdrant/qdrant

# Option 2: Use Qdrant Cloud (update QDRANT_URL and QDRANT_API_KEY in .env)
```

### Step 4: Run the Application

```bash
   # Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# The application will be available at:
# - API:  # - Interactive docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## 🎯 Usage Guide

### 1. Invoice Analysis

**Endpoint**: `POST /api/v1/analyze-invoices`

Upload invoices for analysis:

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-invoices" \\
  -F "employee_name=John Doe" \\
  -F "policy_file=@hr_policy.pdf" \\
  -F "invoices_zip=@invoices.zip"
```

**Request Parameters**:

- `employee_name`: Name of the employee (form field)
- `policy_file`: HR reimbursement policy PDF file
- `invoices_zip`: ZIP file containing invoice PDFs

**Response**:

```json
{
  "success": true,
  "message": "Processed 3 invoices successfully",
  "employee_name": "John Doe",
  "total_invoices": 3,
  "processed_invoices": 3,
  "failed_invoices": 0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Chatbot Queries

**Endpoint**: `POST /api/v1/chat`

Query processed invoices using natural language:

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Show me all declined invoices for John Doe",
    "session_id": "user123",
    "include_sources": true
  }'
```

**Request Body**:

```json
{
  "query": "Show me all declined invoices for John Doe",
  "session_id": "user123",
  "filters": {
    "employee_name": "John Doe",
    "status": "declined"
  },
  "include_sources": true
}
```

**Response**:

```json
{
  "response": "I found 2 declined invoices for John Doe:\\n\\n**Invoice 1**: office_supplies.pdf\\n- **Status**: Declined\\n- **Reason**: Office supplies exceed monthly limit\\n- **Amount**: $150.00\\n\\n**Invoice 2**: restaurant_bill.pdf\\n- **Status**: Declined\\n- **Reason**: Personal meal expenses not reimbursable\\n- **Amount**: $85.00",
  "session_id": "user123",
  "sources": [
    {
      "document_id": "uuid-1",
      "filename": "office_supplies.pdf",
      "employee_name": "John Doe",
      "status": "declined",
      "similarity_score": 0.95
    }
  ],
  "retrieved_documents": 2,
  "query_type": "employee_specific",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 3. Example Queries

The chatbot supports various types of natural language queries:

```bash
# Employee-specific queries
"Show me all invoices for John Doe"
"What is the total reimbursement amount for Jane Smith?"

# Status-based queries  
"List all declined invoices"
"Show me approved expenses from last month"

# General queries
"What are the most common policy violations?"
"Show me invoices over $500"
"Summarize reimbursement statistics"
```

## 🎯 Streaming Invoice Analysis (NEW)

The system now supports **real-time streaming** for invoice analysis processing, providing immediate feedback during PDF processing and LLM analysis.

### Streaming Features

1. **Real-time Progress Updates**: Live progress tracking for each invoice
2. **PDF Processing Streaming**: Real-time feedback during text extraction
3. **LLM Analysis Streaming**: Token-by-token analysis results
4. **Vector Storage Updates**: Progress updates during database storage
5. **Individual Results**: Streaming results for each processed invoice
6. **Error Handling**: Real-time error reporting with detailed messages

### Streaming Endpoints

- **`POST /api/v1/analyze-invoices-stream`**: Stream invoice analysis with real-time updates
- **`POST /api/v1/chat/stream`**: Stream chatbot responses for invoice queries

### Streaming Response Format

The streaming endpoints use Server-Sent Events (SSE) with structured JSON chunks:

```json
{
  "type": "progress|invoice_analysis|result|error|done",
  "data": {...},
  "timestamp": "2024-06-20T10:30:00Z"
}
```

### Example Usage

```python
# Stream invoice analysis
async with StreamingInvoiceAnalysisClient() as client:
    response = await client.analyze_invoices_streaming("John Doe")
    client.print_analysis_summary(response)
```

See `streaming_invoice_analysis_client.py` for a complete example.

## 🛠️ Technical Details

### LLM Integration

The system uses **Google Gemini** through LangChain for:

1. **Invoice Analysis**:

   - Structured prompts for policy compliance checking
   - JSON-formatted responses with detailed reasoning
   - Error handling and fallback responses
2. **Chatbot Responses**:

   - RAG-based response generation
   - Context-aware conversations
   - Markdown-formatted responses

### Vector Database Design

**Qdrant Collection Structure**:

- **Vectors**: 384-dimensional embeddings (all-MiniLM-L6-v2)
- **Metadata**: Employee name, status, amounts, dates, policy violations
- **Content**: Combined invoice text and analysis results
- **Distance Metric**: Cosine similarity

### Prompt Engineering

#### Invoice Analysis Prompt

The system uses a carefully crafted prompt that:

- Provides clear analysis guidelines
- Specifies output format (JSON)
- Includes policy compliance rules
- Handles edge cases and errors

#### Chatbot System Prompt

The chatbot prompt:

- Defines assistant capabilities
- Specifies response formatting (Markdown)
- Provides context handling instructions
- Ensures accurate information retrieval

### Error Handling & Logging

- **Comprehensive logging** at DEBUG, INFO, WARNING, and ERROR levels
- **Graceful error handling** with user-friendly error messages
- **File validation** for uploads and processing
- **API error responses** with appropriate HTTP status codes

## 🔧 Configuration

### Application Settings

All settings are managed through environment variables:

```python
# Core settings
APP_NAME=Invoice Reimbursement System
DEBUG=True
LOG_LEVEL=INFO

# API Keys  
GOOGLE_API_KEY=your_key_here

# Vector Database
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=invoice_reimbursements
EMBEDDING_MODEL=all-MiniLM-L6-v2

# File Processing
MAX_FILE_SIZE=50  # MB
UPLOAD_DIRECTORY=uploads
```

### Logging Configuration

Logs are written to:

- **Console**: INFO level and above
- **File**: DEBUG level and above (`logs/app_YYYYMMDD.log`)
- **Rotation**: 10MB files, 5 backups

## 🚀 Optional Enhancements

### Implemented Features

- **Advanced Error Handling**: Comprehensive error handling and logging
- **Batch Processing**: Concurrent processing of multiple invoices with semaphore limiting

### Future Enhancements

- **Authentication & Authorization**: User management and access control
- **Database Persistence**: Replace in-memory conversation storage with database
- **Advanced Analytics**: Detailed statistics and reporting dashboard
- **Email Notifications**: Automated notifications for processing results
- **Multi-tenancy**: Support for multiple organizations

## 🧪 Testing

### Manual Testing

1. **Health Check**:

    ```bash
    curl http://localhost:8000/health
    ```

2. **Invoice Analysis Test**:

   - Prepare a sample HR policy PDF
   - Create a ZIP file with sample invoice PDFs
   - Use the `/analyze-invoices` endpoint
3. **Chatbot Test**:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{
    "messages": [
        {"role": "user", "content": "Show me all invoices for John Doe"}
    ]
}'
   - Process some invoices first
   - Use the `/chat` endpoint with various queries
```

### API Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🤝 Development

### Project Structure

```text
app/
├── **init**.py
├── main.py                 # FastAPI application setup
├── api/
│   └── routes/
│       ├── invoice_analysis.py  # Invoice processing endpoint
│       └── chatbot.py           # Chat endpoint
├── core/
│   ├── config.py          # Configuration settings
│   └── logging_config.py  # Logging setup
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   ├── pdf_processor.py   # PDF text extraction
│   ├── llm_service.py     # LLM interactions
│   ├── vector_store.py    # Qdrant vector database
│   └── chatbot_service.py # RAG chatbot logic
└── utils/
    └── file_utils.py      # File handling utilities
```

### Code Style

- **Type hints** throughout the codebase
- **Comprehensive docstrings** for all functions
- **Error handling** with appropriate logging
- **Modular design** with clear separation of concerns

## 📝 License

This project is developed as part of an assignment for invoice reimbursement system development.

## 🆘 Troubleshooting

### Common Issues

1. **Qdrant Connection Error**:

   - Ensure Qdrant is running on the configured URL
   - Check firewall settings
   - Verify API key for cloud instances
2. **Gemini API Error**:

   - Verify API key is correct and active
   - Check API quotas and rate limits
   - Ensure billing is enabled (if using paid tier)
3. **PDF Processing Errors**:

   - Ensure PDFs are not encrypted
   - Check file format and corruption
   - Verify file size limits
4. **Memory Issues**:

   - Reduce batch processing concurrency
   - Increase system memory allocation
   - Consider processing smaller file batches

### Support

For technical issues:

1. Check the logs in the `logs/` directory
2. Verify environment variable configuration
3. Test with sample files first
4. Review API documentation at `/docs`

---

#### Built with ❤️ using FastAPI, LangChain, and modern AI technologies
