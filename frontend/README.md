# Frontend Setup and Usage Guide

## Overview

The Streamlit frontend provides an intuitive web interface for the Invoice Reimbursement System. It allows users to upload invoices, analyze them against HR policies, and interact with the results through a conversational AI interface.

## Features

### 📄 Invoice Analysis Page

- **File Upload**: Upload HR policy PDFs and invoice ZIP files
- **Real-time Processing**: Watch the analysis progress in real-time
- **AI-Powered Analysis**: Leverages Gemini AI for intelligent invoice processing
- **Detailed Results**: View comprehensive analysis results with explanations

### 💬 Chat with Invoices Page

- **Natural Language Queries**: Ask questions about your processed invoices
- **Intelligent Responses**: Get AI-powered answers with source citations
- **Advanced Filtering**: Filter results by employee, status, amount, etc.
- **Conversation History**: Maintain context across multiple queries

### 🎨 Modern UI

- **iAI Solutions Theme**: Professional purple-themed interface
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live status indicators and progress bars
- **Interactive Elements**: Clickable suggestions and expandable sections

## Prerequisites

1. **Python Environment**: Python 3.8+ with required packages
2. **Backend Service**: FastAPI server running on port 8000
3. **Dependencies**: Install requirements from `requirements.txt`

## Installation

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend Service**:

   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start Frontend**:

   ```bash
   streamlit run streamlit_app.py
   ```

## Usage Guide

### Getting Started

1. **Launch the Application**
   - Open your browser to `http://localhost:8501`
   - The app will show the system status in the sidebar

2. **Check Backend Status**
   - Ensure the backend shows "✅ Backend Online" in the sidebar
   - If offline, start the FastAPI server first

3. **Upload Documents**
   - Click "Get Started" on the Invoice Analysis page
   - Provide the employee name
   - Upload HR policy PDF file
   - Upload ZIP file containing invoices

4. **Monitor Analysis**
   - Watch real-time progress updates
   - View individual invoice results as they're processed
   - Check for any errors or warnings

5. **Review Results**
   - View summary statistics
   - Expand individual invoice details
   - Check policy violations and reimbursement amounts

6. **Chat with Results**
   - Switch to the Chat page
   - Ask questions about the processed invoices
   - Use filters to narrow down results
   - Try suggested questions for ideas

### Example Queries for Chat

- "Show me all declined invoices"
- "What are the most expensive invoices?"
- "Which employees have policy violations?"
- "Summarize the reimbursement statistics"
- "Show me invoices over ₹5000"

### Troubleshooting

#### Backend Connection Issues

- **Error**: "Backend Offline"
- **Solution**: Start the FastAPI server: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

#### File Upload Issues

- **Error**: File size too large
- **Solution**: Check that files are under 200MB, compress if needed

#### Analysis Errors

- **Error**: "Service Overloaded"
- **Solution**: Wait a few minutes and try again, or process fewer files at once

#### Import Errors

- **Error**: Module not found
- **Solution**: Ensure you're running from the correct directory and all dependencies are installed

## Configuration

### Streamlit Settings

The app uses `.streamlit/config.toml` for configuration:

- Theme colors (iAI Solutions purple theme)
- Upload size limits
- Server settings

### Environment Variables

- `STREAMLIT_API_BASE_URL`: Backend API URL (default: <http://localhost:8000>)
- `STREAMLIT_API_TIMEOUT`: Request timeout (default: 300 seconds)
- `STREAMLIT_DEFAULT_CURRENCY`: Default currency (default: INR)

## File Structure

```
frontend/
├── streamlit_app.py          # Main application entry point
├── pages/
│   ├── invoice_analysis.py   # Invoice analysis page
│   └── chat_with_invoices.py # Chat interface page
├── utils/
│   ├── streamlit_utils.py    # Utility functions
│   └── theme.py             # iAI Solutions theme
└── config/
    └── streamlit_config.py   # Configuration settings
```

## Performance Tips

1. **File Optimization**
   - Use compressed ZIP files for invoices
   - Ensure PDFs are not corrupted or password-protected
   - Process 5-10 invoices at a time for best performance

2. **System Resources**
   - The AI analysis is resource-intensive
   - Allow adequate time for processing
   - Monitor system resources during analysis

3. **Network Considerations**
   - Ensure stable internet connection
   - Files are uploaded to the backend for processing
   - Chat responses are streamed in real-time

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify backend service is running
3. Check application logs for detailed error messages
4. Ensure all dependencies are properly installed

## Development

### Customization

- Modify themes in `utils/theme.py`
- Add new pages in the `pages/` directory
- Update configuration in `config/streamlit_config.py`

### Adding Features

- Follow the existing page structure
- Use the shared utilities for consistency
- Maintain the iAI Solutions theme
- Add proper error handling and user feedback
