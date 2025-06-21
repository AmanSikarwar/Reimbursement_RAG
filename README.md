# 📄 Invoice Reimbursement System

A comprehensive AI-powered invoice reimbursement analysis system built with FastAPI, LangChain, and Gemini LLM. This system uses RAG (Retrieval Augmented Generation) to analyze invoice documents against HR policies and provides an intelligent chatbot interface for querying processed invoices.

## 🚀 Features

- **Intelligent Invoice Analysis**: Analyze PDF invoices against HR reimbursement policies using Gemini LLM
- **Vector-Based Storage**: Store and retrieve invoice embeddings using Qdrant vector database
- **RAG Chatbot**: Interactive chatbot for querying processed invoices using natural language
- **Batch Processing**: Process multiple invoices at once via ZIP file upload
- **Duplicate Detection**: Prevent duplicate processing of the same invoices
- **Streaming Responses**: Real-time streaming for both analysis and chat responses
- **Modern UI**: Clean, responsive Streamlit frontend with session management
- **Comprehensive API**: RESTful API with FastAPI for backend operations

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │    │   FastAPI API   │    │  Gemini LLM     │
│  (Frontend)     │◄──►│   (Backend)     │◄──►│  (Analysis)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Qdrant Vector  │    │  PDF Processor  │
                       │  Database       │    │  (Text Extract) │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

### Backend

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for developing applications with LLMs
- **Gemini**: Google's advanced LLM for invoice analysis
- **Qdrant**: Vector database for storing and retrieving embeddings
- **Sentence-Transformers**: For generating text embeddings
- **PyPDF2**: PDF text extraction
- **Pydantic**: Data validation and serialization

### Frontend

- **Streamlit**: Web application framework for data science
- **Streamlit-Chat**: Chat interface components

### Infrastructure

- **Docker & Docker Compose**: Complete containerization solution
- **Qdrant**: Vector database (containerized)
- **Multi-stage Docker builds**: Optimized production images
- **Health checks**: Automated service monitoring

## 🐳 Docker Deployment (Recommended)

The easiest way to run the Invoice Reimbursement System is using Docker. This method handles all dependencies and services automatically.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0 or higher)
- At least 4GB RAM available for Docker
- [Gemini API Key](https://aistudio.google.com/app/apikey)

### Quick Start with Docker

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd Reimbursement_RAG
   ```

2. **Set up environment variables**:

   ```bash
   # Copy the environment template
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   nano .env  # or use your preferred editor
   ```

3. **Run the complete setup**:

   ```bash
   # Make the setup script executable and run it
   chmod +x docker-setup.sh
   ./docker-setup.sh setup
   ```

   This single command will:
   - Check Docker installation
   - Build all necessary images
   - Start all services (Qdrant, Backend, Frontend)
   - Perform health checks

4. **Access the application**:
   - **Frontend**: <http://localhost:8501>
   - **Backend API**: <http://localhost:8000>
   - **API Documentation**: <http://localhost:8000/docs>
   - **Qdrant Dashboard**: <http://localhost:6333/dashboard>

### Docker Management Commands

The `docker-setup.sh` script provides convenient commands for managing your Docker environment:

```bash
# Initial setup (build and start everything)
./docker-setup.sh setup

# Start services in production mode
./docker-setup.sh start

# Start services in development mode (with hot reload)
./docker-setup.sh start-dev

# Stop all services
./docker-setup.sh stop

# View service status and URLs
./docker-setup.sh status

# View logs (all services)
./docker-setup.sh logs

# View logs for specific service
./docker-setup.sh logs backend
./docker-setup.sh logs frontend
./docker-setup.sh logs qdrant

# Restart services
./docker-setup.sh restart

# Clean up Docker resources
./docker-setup.sh cleanup

# Complete reset (removes volumes and rebuilds)
./docker-setup.sh reset

# Show help
./docker-setup.sh help
```

### Docker Architecture

The Docker setup includes three main services:

```text
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit UI      │    │    FastAPI API      │    │    Qdrant Vector    │
│   (Port 8501)       │◄──►│    (Port 8000)      │◄──►│    (Port 6333)      │
│   invoice-frontend  │    │   invoice-backend   │    │   invoice-qdrant    │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### Development vs Production

- **Production mode** (`docker-compose.yml`): Optimized images, no hot reload
- **Development mode** (`docker-compose.dev.yml`): Code mounting, hot reload enabled

### Troubleshooting Docker Setup

**Services not starting:**

```bash
# Check service logs
./docker-setup.sh logs

# Check Docker system
docker system df
docker system prune -f
```

**Port conflicts:**

```bash
# Check what's using the ports
lsof -i :8000  # Backend port
lsof -i :8501  # Frontend port
lsof -i :6333  # Qdrant port
```

**Memory issues:**

```bash
# Check Docker memory usage
docker stats

# Increase Docker memory in Docker Desktop settings
# Recommended: At least 4GB RAM for Docker
```

## 💻 Local Development Setup (Alternative)

If you prefer to run without Docker, follow these steps:

## 📋 Prerequisites

- Python 3.9 or higher
- Docker (for Qdrant vector database)
- Google API Key for Gemini LLM access

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Reimbursement_RAG
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Gemini API Key (REQUIRED)
GOOGLE_API_KEY=your_gemini_api_key_here

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local Docker instance

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
```

### 5. Start Qdrant Vector Database

```bash
# Start Qdrant using Docker
docker run -p 6333:6333 -d --name qdrant qdrant/qdrant

# Or use the VS Code task
# Command Palette > Tasks: Run Task > Start Qdrant with Docker
```

### 6. Initialize the Application

```bash
# Verify setup
python verify_setup.py

# Check configuration
python check_setup.py
```

## 🚀 Quick Start

### Option 1: Using VS Code Tasks (Recommended)

1. Open VS Code in the project directory
2. Press `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
3. Select "Tasks: Run Task"
4. Choose "Build and Run Invoice Reimbursement System"

### Option 2: Manual Start

#### Start Backend (FastAPI)

```bash
# From project root
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Start Frontend (Streamlit)

```bash
# In a new terminal
./venv/bin/python -m streamlit run streamlit_app.py --server.port 8501
```

### Option 3: Using Available Tasks

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (in another terminal)
python -m streamlit run streamlit_app.py --server.port 8501
```

## 📱 Usage

### 1. Access the Application

- **Frontend**: <http://localhost:8501>
- **Backend API**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>

### 2. Invoice Analysis

1. Navigate to the "📄 Invoice Analysis" page
2. Enter employee name
3. Upload HR reimbursement policy (PDF)
4. Upload invoices (ZIP file containing PDFs)
5. Click "🔍 Start Analysis"
6. View results with detailed breakdown

### 3. Chat with Invoices

1. Navigate to the "💬 Chat with Invoices" page
2. Ask questions about processed invoices
3. Use natural language queries like:
   - "Show me all declined invoices"
   - "What invoices did John submit?"
   - "List all partially reimbursed expenses"

## 🔍 API Endpoints

### Health Check

- `GET /health` - Application health status
- `GET /api/v1/health/detailed` - Detailed health check

### Invoice Analysis

- `POST /api/v1/analyze-invoices` - Analyze invoices against policy
- `POST /api/v1/analyze-invoices-stream` - Streaming analysis
- `GET /api/v1/analysis-status` - Get analysis status

### Chatbot

- `POST /api/v1/chat` - Chat with processed invoices
- `POST /api/v1/chat/stream` - Streaming chat responses
- `GET /api/v1/chat/history/{session_id}` - Get chat history
- `DELETE /api/v1/chat/history/{session_id}` - Clear chat history

## 📁 Project Structure

```text
Reimbursement_RAG/
├── app/                          # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes
│   │   └── routes/
│   │       ├── health.py         # Health check endpoints
│   │       ├── invoice_analysis.py # Invoice analysis endpoints
│   │       └── chatbot.py        # Chat endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Application settings
│   │   └── logging_config.py     # Logging configuration
│   ├── models/                   # Data models
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/                 # Business logic
│   │   ├── llm_service.py        # Gemini LLM integration
│   │   ├── vector_store.py       # Qdrant operations
│   │   ├── pdf_processor.py      # PDF text extraction
│   │   └── chatbot_service.py    # RAG chatbot logic
│   └── utils/                    # Utilities
│       ├── file_utils.py         # File handling utilities
│       └── responses.py          # Response utilities
├── frontend/                     # Streamlit Frontend
│   ├── streamlit_app.py          # Main Streamlit app
│   ├── pages/                    # Streamlit pages
│   │   ├── invoice_analysis.py   # Invoice analysis page
│   │   └── chat_with_invoices.py # Chat page
│   └── utils/                    # Frontend utilities
│       ├── streamlit_utils.py    # Streamlit helpers
│       └── theme.py              # UI theme configuration
├── logs/                         # Application logs
├── uploads/                      # File uploads storage
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── streamlit_app.py              # Entry point for Streamlit
├── verify_setup.py               # Setup verification script
└── check_setup.py                # Configuration check script
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | - | ✅ |
| `QDRANT_URL` | Qdrant database URL | `http://localhost:6333` | ✅ |
| `QDRANT_API_KEY` | Qdrant API key | - | 🔄 |
| `DEBUG` | Enable debug mode | `false` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `COLLECTION_NAME` | Qdrant collection name | `invoice_reimbursements` | ❌ |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` | ❌ |
| `MAX_FILE_SIZE` | Max upload size (MB) | `50` | ❌ |
| `LLM_MODEL` | Gemini model name | `gemini-2.5-flash` | ❌ |
| `LLM_TEMPERATURE` | LLM temperature | `0.1` | ❌ |

### VS Code Tasks

The project includes predefined VS Code tasks for common operations:

- **Setup Python Environment**: Create virtual environment
- **Install Dependencies**: Install Python packages
- **Start Qdrant with Docker**: Launch Qdrant container
- **Run FastAPI Server**: Start backend server
- **Run Streamlit Frontend**: Start frontend application
- **Build and Run**: Complete application startup

## 📊 Logging

The application uses structured logging with:

- **File Logging**: Logs stored in `logs/` directory
- **Console Logging**: Development-friendly console output
- **Log Rotation**: Daily log file rotation
- **Structured Format**: JSON-formatted logs for production

## 🔒 Security

### Production Considerations

- Set `DEBUG=false` in production
- Configure specific `ALLOWED_HOSTS`
- Use environment variables for all secrets
- Implement proper authentication/authorization
- Use HTTPS in production
- Secure file upload validation

### File Upload Security

- File type validation
- File size limits
- Sanitized file names
- Secure storage paths

## 🧪 Testing

### Verify Installation

```bash
python verify_setup.py
```

### Check Configuration

```bash
python check_setup.py
```

### Manual Testing

1. Start the application
2. Upload sample invoices
3. Test chat functionality
4. Verify vector storage

## 🐛 Troubleshooting

### Common Issues

#### 1. Qdrant Connection Error

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker restart qdrant
```

#### 2. Gemini API Error

- Verify `GOOGLE_API_KEY` in `.env`
- Check API key permissions
- Ensure billing is enabled

#### 3. Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

#### 4. Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true python -m uvicorn app.main:app --reload
```

## 🔧 Development

### Adding New Features

1. Create feature branch
2. Add service logic in `app/services/`
3. Add API endpoint in `app/api/routes/`
4. Update Pydantic schemas in `app/models/schemas.py`
5. Add frontend page in `frontend/pages/`
6. Update documentation

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Add comprehensive docstrings
- Implement proper error handling

### Testing

```bash
# Run manual tests
python verify_setup.py

# Check code quality
ruff check .
```

## 📈 Performance

### Optimization Tips

- Use streaming for large responses
- Implement caching for repeated queries
- Optimize vector search parameters
- Use batch processing for multiple files

### Monitoring

- Check application logs in `logs/`
- Monitor Qdrant memory usage
- Track API response times
- Monitor file upload sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Check API documentation at `/docs`

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - Invoice analysis with Gemini LLM
  - Vector storage with Qdrant
  - RAG chatbot interface
  - Streamlit frontend
  - Comprehensive API

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [LangChain Documentation](https://python.langchain.com/)

---

Made with ❤️ using Python, FastAPI, and AI technologies
