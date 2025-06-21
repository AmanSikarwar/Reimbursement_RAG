"""
Invoice Analysis API Routes.

This module handles the invoice analysis endpoint that processes PDF invoices
against HR policies using LLMs and stores results in the vector database.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    InvoiceAnalysisProgress,
    InvoiceAnalysisResponse,
    InvoiceAnalysisStreamingChunk,
    InvoiceAnalysisStreamingChunkType,
)
from app.services.llm_service import LLMService
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import VectorStoreService
from app.utils.file_utils import (
    extract_zip_file,
    generate_file_hash_from_path,
    generate_upload_file_hash,
    sanitize_filename,
    save_uploaded_file,
    validate_file,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_vector_store(request: Request) -> VectorStoreService:
    """Dependency to get vector store service from app state."""
    return request.app.state.vector_store


@router.post(
    "/analyze-invoices",
    response_model=InvoiceAnalysisResponse,
    summary="Analyze Employee Invoice Reimbursements",
    description="""
**AI-powered invoice analysis against HR reimbursement policies with comprehensive processing pipeline.**
    
This endpoint processes employee expense invoices using advanced AI to determine reimbursement eligibility
based on company HR policies. The system provides detailed analysis, policy compliance checking, and
stores results for future querying via the chatbot interface.
    
## Processing Workflow
    
### 1. **File Validation & Upload** (5-10 seconds)
- Validates policy PDF format and size limits
- Validates invoices ZIP structure and contents
- Performs security checks on uploaded files
- Extracts and prepares files for processing
    
### 2. **Policy Analysis** (10-20 seconds)
- Extracts and parses HR policy document text
- Identifies reimbursement rules and limits
- Creates policy knowledge base for comparison
    
### 3. **Invoice Processing** (30-60 seconds per invoice)
- Extracts text and metadata from each PDF
- Uses Gemini LLM for intelligent content analysis
- Identifies amounts, dates, categories, and vendors
- Detects potential duplicate submissions
    
### 4. **Policy Compliance Check** (20-30 seconds per invoice)
- Compares invoice details against policy rules
- Calculates reimbursable amounts per category
- Identifies policy violations and exceptions
- Generates detailed reasoning for decisions
    
### 5. **Vector Storage** (5-15 seconds)
- Creates embeddings for searchable content
- Stores analysis results in Qdrant database
- Enables future chatbot queries and analytics
    
## Response Details
    
### Processing Summary
- Total invoices processed and success/failure counts
- Aggregate amounts and reimbursement totals
- Processing time and performance metrics
- Duplicate detection results
    
### Individual Results
- Per-invoice analysis with detailed breakdowns
- Reimbursement status (fully/partially/declined)
- Policy violation details and explanations
- Amount categorization and calculations
    
## Error Handling
    
The system provides detailed error reporting for:
- Invalid file formats or corrupted uploads
- Policy parsing failures
- Invoice processing errors
- LLM service availability issues
- Vector database connectivity problems
    
## Best Practices
    
- **File Organization**: Use clear, descriptive filenames
- **Policy Updates**: Re-upload policy if rules change
- **Batch Size**: Process 10-50 invoices per batch for optimal performance
- **Naming Convention**: Include employee ID or department in filenames
- **File Quality**: Ensure PDFs are text-searchable, not scanned images
    
---
    
**Pro Tip**: For large batches, consider using the streaming endpoint `/analyze-invoices/stream` 
to get real-time progress updates during processing.
""",
    response_description="Comprehensive analysis results with processing summary and individual invoice details",
    responses={
        200: {
            "description": "Invoice analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Successfully processed 3 invoices for Aman Sikarwar",
                        "employee_name": "Aman Sikarwar",
                        "total_invoices": 3,
                        "processed_invoices": 3,
                        "failed_invoices": 0,
                        "processing_time_seconds": 45.2,
                        "summary": {
                            "total_amount": 15000.0,
                            "total_reimbursement": 12500.0,
                            "fully_reimbursed_count": 2,
                            "partially_reimbursed_count": 1,
                            "declined_count": 0,
                            "policy_violations_count": 1,
                            "duplicate_count": 0
                        },
                        "results": [
                            {
                                "filename": "travel_receipt_001.pdf",
                                "status": "fully_reimbursed",
                                "reason": "Business travel expense within policy limits. Hotel stay approved for client meeting in Mumbai.",
                                "total_amount": 5000.0,
                                "reimbursement_amount": 5000.0,
                                "currency": "INR",
                                "categories": ["accommodation", "business_travel"],
                                "policy_violations": None,
                                "from_cache": False
                            },
                            {
                                "filename": "meal_receipt_002.pdf",
                                "status": "partially_reimbursed",
                                "reason": "Meal expense partially approved. Alcohol charges excluded per company policy.",
                                "total_amount": 3000.0,
                                "reimbursement_amount": 2500.0,
                                "currency": "INR",
                                "categories": ["meals", "entertainment"],
                                "policy_violations": ["alcohol_charges_excluded"],
                                "from_cache": False
                            }
                        ],
                        "processing_errors": [],
                        "timestamp": "2024-12-21T10:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - Invalid file format, size exceeded, or malformed data",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_file_format": {
                            "summary": "Invalid file format",
                            "value": {
                                "success": False,
                                "error": "validation_error",
                                "message": "Invalid file format",
                                "details": [
                                    {
                                        "code": "INVALID_FORMAT",
                                        "message": "Policy file must be PDF format",
                                        "field": "policy_file"
                                    }
                                ]
                            }
                        },
                        "file_size_exceeded": {
                            "summary": "File size limit exceeded",
                            "value": {
                                "success": False,
                                "error": "file_size_error",
                                "message": "File size exceeds maximum limit of 50MB"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error in request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "validation_error",
                        "message": "Request validation failed",
                        "details": [
                            {
                                "code": "MISSING_FIELD",
                                "message": "Employee name is required",
                                "field": "employee_name"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during processing",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "processing_error",
                        "message": "Error during invoice analysis processing",
                        "details": [
                            {
                                "code": "LLM_SERVICE_ERROR",
                                "message": "Gemini API temporarily unavailable"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def analyze_invoices(
    request: Request,
    employee_name: str = Form(
        ..., 
        description="Name of the employee submitting invoices for reimbursement analysis",
        example="Aman Sikarwar",
        min_length=2,
        max_length=100,
        title="Employee Name"
    ),
    policy_file: UploadFile = File(
        ..., 
        description="HR reimbursement policy PDF file (max 50MB). Should contain clear policy rules, limits, and guidelines.",
        title="HR Policy PDF",
        alias="policy_file"
    ),
    invoices_zip: UploadFile = File(
        ..., 
        description="ZIP archive containing invoice PDF files (max 50MB). Each PDF should be a clear, readable invoice document.",
        title="Invoices ZIP Archive",
        alias="invoices_zip"
    ),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> InvoiceAnalysisResponse:
    """
    Analyze employee invoices against HR reimbursement policy using AI.

    This comprehensive endpoint processes employee expense invoices using advanced AI analysis
    to determine reimbursement eligibility based on company HR policies. The system performs
    intelligent document analysis, policy compliance checking, and stores structured results
    for future querying and analytics.

    ## Processing Details

    ### Document Analysis
    - **Policy Parsing**: Extracts and interprets HR policy rules and limits
    - **Invoice OCR**: Reads and processes invoice text, amounts, and metadata
    - **Content Validation**: Ensures documents are readable and complete
    - **Duplicate Detection**: Identifies potentially duplicate submissions

    ### AI Analysis Pipeline
    - **Gemini LLM Integration**: Uses Google's advanced language model
    - **Contextual Understanding**: Analyzes business context and compliance
    - **Rule Application**: Applies policy rules to individual line items
    - **Decision Reasoning**: Provides detailed explanations for all decisions

    ### Storage & Indexing
    - **Vector Database**: Stores embeddings for semantic search
    - **Metadata Indexing**: Enables filtering and categorization
    - **Audit Trail**: Maintains complete processing history

    Args:
        employee_name (str): Full name of the employee submitting invoices.
            Must be 2-100 characters. Used for attribution and filtering.
        policy_file (UploadFile): PDF file containing the HR reimbursement policy.
            Must be valid PDF format, max 50MB. Should include:
            - Reimbursement categories and limits
            - Approval workflows and requirements
            - Excluded items and restrictions
            - Documentation requirements
        invoices_zip (UploadFile): ZIP archive containing invoice PDF files.
            Must be valid ZIP format, max 50MB. Each PDF should be:
            - Clear and readable (not scanned image)
            - Complete invoice with all details
            - Proper business expense documentation
        vector_store (VectorStoreService): Injected vector database service
            for storing analysis results and enabling future queries.

    Returns:
        InvoiceAnalysisResponse: Comprehensive analysis results including:
            - Processing summary with counts and totals
            - Individual invoice analysis results
            - Reimbursement decisions with detailed reasoning
            - Policy compliance status and violations
            - Error details for any failed processing

    Raises:
        HTTPException: 
            - 400: Invalid file format, size exceeded, or corrupted files
            - 422: Validation error in request parameters
            - 500: Internal processing errors (LLM API, database, etc.)

    Example:
        ```python
        # Using requests library
        files = {
            'policy_file': ('policy.pdf', open('policy.pdf', 'rb'), 'application/pdf'),
            'invoices_zip': ('invoices.zip', open('invoices.zip', 'rb'), 'application/zip')
        }
        data = {'employee_name': 'Aman Sikarwar'}
        response = requests.post('/api/v1/analyze-invoices', files=files, data=data)
        ```

    Performance Notes:
        - Processing time scales with number of invoices (2-5 minutes per invoice)
        - Large batches are processed sequentially to maintain quality
        - Results are cached to prevent duplicate processing
        - Vector storage enables fast future queries via chatbot
    """
    logger.info(f"Starting invoice analysis for employee: {employee_name}")

    try:
        await validate_file(policy_file, ["pdf"])
        await validate_file(invoices_zip, ["zip"])

        pdf_processor = PDFProcessor()
        llm_service = LLMService()

        with tempfile.TemporaryDirectory() as temp_dir:
            policy_hash = await generate_upload_file_hash(policy_file)

            existing_policy = await vector_store.check_file_exists(
                policy_hash, "policy"
            )

            if existing_policy:
                logger.info(
                    f"Policy file already exists in vector store with hash: {policy_hash}"
                )
                policy_text = existing_policy.content
            else:
                policy_path = await save_uploaded_file(policy_file, temp_dir)
                policy_text = await pdf_processor.extract_text(policy_path)

                if not policy_text.strip():
                    raise HTTPException(
                        status_code=400, detail="Could not extract text from policy PDF"
                    )

                try:
                    await vector_store.store_policy_document(
                        policy_text=policy_text,
                        policy_name=f"HR_Policy_{employee_name}_{datetime.now().strftime('%Y%m%d')}",
                        organization="Company",
                        file_hash=policy_hash,
                    )
                    logger.info(
                        f"New policy document stored in vector database for {employee_name}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to store policy in vector database: {e}")

            zip_path = await save_uploaded_file(invoices_zip, temp_dir)
            invoice_files = await extract_zip_file(zip_path, temp_dir)

            if not invoice_files:
                raise HTTPException(
                    status_code=400, detail="No PDF files found in the ZIP archive"
                )

            analysis_results = []
            processing_errors = []

            semaphore = asyncio.Semaphore(5)

            async def process_single_invoice(invoice_path: str):
                async with semaphore:
                    try:
                        return await _process_invoice(
                            invoice_path,
                            policy_text,
                            employee_name,
                            pdf_processor,
                            llm_service,
                            vector_store,
                        )
                    except Exception as e:
                        logger.error(f"Error processing invoice {invoice_path}: {e}")
                        processing_errors.append(
                            {"file": os.path.basename(invoice_path), "error": str(e)}
                        )
                        return None

            tasks = [
                process_single_invoice(invoice_path) for invoice_path in invoice_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if result and not isinstance(result, Exception):
                    analysis_results.append(result)

            response = InvoiceAnalysisResponse(
                success=True,
                message=f"Processed {len(analysis_results)} invoices successfully",
                employee_name=employee_name,
                total_invoices=len(invoice_files),
                processed_invoices=len(analysis_results),
                failed_invoices=len(processing_errors),
                results=analysis_results,
                processing_errors=processing_errors if processing_errors else None,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(
                f"Invoice analysis completed for {employee_name}. "
                f"Processed: {len(analysis_results)}, Failed: {len(processing_errors)}"
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in invoice analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during invoice analysis: {str(e)}",
        )


async def _process_invoice(
    invoice_path: str,
    policy_text: str,
    employee_name: str,
    pdf_processor: PDFProcessor,
    llm_service: LLMService,
    vector_store: VectorStoreService,
) -> dict:
    """
    Process a single invoice file.

    Args:
        invoice_path: Path to the invoice PDF file
        policy_text: HR policy text
        employee_name: Name of the employee
        pdf_processor: PDF processor service
        llm_service: LLM service
        vector_store: Vector store service

    Returns:
        Dictionary containing analysis results
    """
    invoice_hash = await generate_file_hash_from_path(invoice_path)

    existing_invoice = await vector_store.check_invoice_exists(
        invoice_hash, employee_name
    )

    if existing_invoice:
        logger.info(
            f"Invoice {os.path.basename(invoice_path)} already processed for {employee_name}"
        )
        analysis_result = existing_invoice.metadata.get("analysis", {})
        return {
            "filename": os.path.basename(invoice_path),
            "status": existing_invoice.metadata.get("status"),
            "reason": existing_invoice.metadata.get("reason"),
            "total_amount": existing_invoice.metadata.get("total_amount"),
            "reimbursement_amount": existing_invoice.metadata.get(
                "reimbursement_amount"
            ),
            "currency": existing_invoice.metadata.get("currency"),
            "categories": existing_invoice.metadata.get("categories"),
            "policy_violations": existing_invoice.metadata.get("policy_violations"),
            "from_cache": True,
        }

    invoice_text = await pdf_processor.extract_text(invoice_path)

    if not invoice_text.strip():
        raise ValueError("Could not extract text from invoice PDF")

    analysis_result = await llm_service.analyze_invoice(
        invoice_text=invoice_text, policy_text=policy_text, employee_name=employee_name
    )

    await vector_store.store_invoice_analysis(
        invoice_text=invoice_text,
        analysis_result=analysis_result,
        employee_name=employee_name,
        invoice_filename=os.path.basename(invoice_path),
        file_hash=invoice_hash,
    )

    return {
        "filename": os.path.basename(invoice_path),
        "status": analysis_result.get("status"),
        "reason": analysis_result.get("reason"),
        "total_amount": analysis_result.get("total_amount"),
        "reimbursement_amount": analysis_result.get("reimbursement_amount"),
        "currency": analysis_result.get("currency"),
        "categories": analysis_result.get("categories"),
        "policy_violations": analysis_result.get("policy_violations"),
        "from_cache": False,
    }


@router.get("/analysis-status")
async def get_analysis_status():
    """
    Get the status of the invoice analysis system.

    Returns:
        System status information
    """
    return {
        "status": "operational",
        "message": "Invoice analysis system is running",
        "timestamp": datetime.now(timezone.utc),
    }


@router.post(
    "/analyze-invoices-stream",
    summary="Analyze Invoices with Streaming",
    description="""
Analyze employee invoices against HR reimbursement policy with real-time streaming updates.
    
This endpoint provides the same functionality as `/analyze-invoices` but with 
real-time streaming updates, allowing clients to track processing progress 
and receive intermediate results as they become available.
    
### Streaming Format:
The response uses Server-Sent Events (SSE) format with JSON chunks:

```
data: {"type": "progress", "data": {"stage": "extracting", "progress": 25}}
data: {"type": "result", "data": {"filename": "invoice1.pdf", "status": "fully_reimbursed"}}
data: {"type": "summary", "data": {"processed": 3, "total_amount": 15000.0}}
data: {"type": "done", "data": {"message": "Analysis complete"}}
```
    
### Chunk Types:
- **progress**: Processing stage updates with percentage
- **result**: Individual invoice analysis results
- **error**: Processing error information
- **summary**: Final processing summary
- **done**: Analysis completion signal
    
### Use Cases:
- Real-time progress tracking in UI
- Large batch processing with feedback
- Progressive result display
""",
    response_description="Server-sent events stream with real-time processing updates",
    responses={
        200: {
            "description": "Streaming analysis progress and results",
            "content": {
                "text/plain": {
                    "example": """data: {"type": "progress", "data": {"stage": "validating", "progress": 10}}
data: {"type": "progress", "data": {"stage": "extracting", "progress": 30}}
data: {"type": "result", "data": {"filename": "invoice1.pdf", "status": "fully_reimbursed"}}
data: {"type": "done", "data": {"processed_invoices": 3}}"""
                }
            }
        },
        400: {"description": "Invalid file format or processing error"},
        422: {"description": "Validation error in request parameters"}
    }
)
async def analyze_invoices_streaming(
    request: Request,
    employee_name: str = Form(
        ..., 
        description="Name of the employee submitting invoices",
        example="Aman Sikarwar"
    ),
    policy_file: UploadFile = File(
        ..., 
        description="HR reimbursement policy PDF file (max 50MB)",
        media_type="application/pdf"
    ),
    invoices_zip: UploadFile = File(
        ..., 
        description="ZIP file containing invoice PDFs (max 50MB)",
        media_type="application/zip"
    ),
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """
    Analyze employee invoices against HR reimbursement policy with streaming updates.

    This endpoint processes a ZIP file containing invoice PDFs and analyzes them
    against the provided HR policy using an LLM with real-time streaming updates.
    Results are stored in the vector database.

    Args:
        employee_name: Name of the employee submitting invoices
        policy_file: PDF file containing HR reimbursement policy
        invoices_zip: ZIP file containing one or more invoice PDFs
        vector_store: Vector store service dependency

    Returns:
        Streaming response with real-time processing updates

    Raises:
        HTTPException: If file validation fails or processing errors occur
    """
    logger.info(f"Starting streaming invoice analysis for employee: {employee_name}")

    try:
        await validate_file(policy_file, ["pdf"])
        await validate_file(invoices_zip, ["zip"])

        logger.info(
            f"Reading file contents for: {policy_file.filename}, {invoices_zip.filename}"
        )

        policy_content = await policy_file.read()
        zip_content = await invoices_zip.read()

        logger.info(
            f"Successfully read file contents: policy={len(policy_content)} bytes, zip={len(zip_content)} bytes"
        )

        policy_filename = policy_file.filename
        zip_filename = invoices_zip.filename

    except Exception as e:
        logger.error(f"Error reading file contents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read uploaded files: {str(e)}"
        )

    async def generate_streaming_analysis():
        """Generate streaming analysis response chunks."""
        try:
            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.METADATA, data={'employee': employee_name, 'status': 'starting'}).model_dump_json()}\n\n"

            pdf_processor = PDFProcessor()
            llm_service = LLMService()

            with tempfile.TemporaryDirectory() as temp_dir:
                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'checking_policy_duplicates'}).model_dump_json()}\n\n"

                from app.utils.file_utils import generate_file_hash

                policy_hash = await generate_file_hash(policy_content)

                existing_policy = await vector_store.check_policy_exists(policy_hash)

                if existing_policy:
                    yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'policy_duplicate_found', 'message': 'Policy already exists, using cached version'}).model_dump_json()}\n\n"
                    policy_text = existing_policy.content
                else:
                    yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'extracting_policy'}).model_dump_json()}\n\n"

                    policy_path = os.path.join(
                        temp_dir, sanitize_filename(policy_filename or "policy.pdf")
                    )

                    async with aiofiles.open(policy_path, "wb") as f:
                        await f.write(policy_content)

                    logger.info(f"Policy file saved: {policy_path}")
                    policy_text = await pdf_processor.extract_text(policy_path)

                    if not policy_text.strip():
                        error_chunk = InvoiceAnalysisStreamingChunk(
                            type=InvoiceAnalysisStreamingChunkType.ERROR,
                            data={"error": "Could not extract text from policy PDF"},
                        )
                        yield f"data: {error_chunk.model_dump_json()}\n\n"
                        return

                    try:
                        await vector_store.store_policy_document(
                            policy_text=policy_text,
                            policy_name=f"HR_Policy_{employee_name}_{datetime.now().strftime('%Y%m%d')}",
                            organization="Company",
                            file_hash=policy_hash,
                        )
                        logger.info(
                            f"New policy document stored in vector database for {employee_name}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to store policy in vector database: {e}"
                        )

                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'completed', 'policy_length': len(policy_text)}).model_dump_json()}\n\n"

                zip_path = os.path.join(
                    temp_dir, sanitize_filename(zip_filename or "invoices.zip")
                )

                async with aiofiles.open(zip_path, "wb") as f:
                    await f.write(zip_content)

                logger.info(f"ZIP file saved: {zip_path}")
                invoice_files = await extract_zip_file(zip_path, temp_dir)

                if not invoice_files:
                    error_chunk = InvoiceAnalysisStreamingChunk(
                        type=InvoiceAnalysisStreamingChunkType.ERROR,
                        data={"error": "No PDF files found in the ZIP archive"},
                    )
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                    return

                total_invoices = len(invoice_files)
                analysis_results = []
                processing_errors = []

                progress = InvoiceAnalysisProgress(
                    current_invoice=0,
                    total_invoices=total_invoices,
                    processed_invoices=0,
                    failed_invoices=0,
                    current_filename=None,
                    stage="starting",
                )
                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                for idx, invoice_path in enumerate(invoice_files, 1):
                    filename = os.path.basename(invoice_path)

                    try:
                        progress.current_invoice = idx
                        progress.current_filename = filename
                        progress.stage = "checking_duplicates"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        invoice_hash = await generate_file_hash_from_path(invoice_path)

                        existing_invoice = await vector_store.check_invoice_exists(
                            invoice_hash, employee_name
                        )

                        if existing_invoice:
                            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_ANALYSIS, data={'filename': filename, 'status': 'duplicate_found', 'message': 'Invoice already processed, returning cached result'}).model_dump_json()}\n\n"

                            result_data = {
                                "filename": filename,
                                "status": existing_invoice.metadata.get("status"),
                                "reason": existing_invoice.metadata.get("reason"),
                                "total_amount": existing_invoice.metadata.get(
                                    "total_amount"
                                ),
                                "reimbursement_amount": existing_invoice.metadata.get(
                                    "reimbursement_amount"
                                ),
                                "currency": existing_invoice.metadata.get("currency"),
                                "categories": existing_invoice.metadata.get(
                                    "categories"
                                ),
                                "policy_violations": existing_invoice.metadata.get(
                                    "policy_violations"
                                ),
                                "from_cache": True,
                            }

                            analysis_results.append(result_data)
                            progress.processed_invoices += 1

                            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.RESULT, data=result_data).model_dump_json()}\n\n"
                            continue

                        progress.stage = "extracting_text"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_EXTRACTION, data={'filename': filename, 'status': 'extracting'}).model_dump_json()}\n\n"

                        invoice_text = await pdf_processor.extract_text(invoice_path)

                        if not invoice_text.strip():
                            raise ValueError("Could not extract text from invoice PDF")

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_EXTRACTION, data={'filename': filename, 'status': 'completed', 'text_length': len(invoice_text)}).model_dump_json()}\n\n"

                        progress.stage = "analyzing"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        analysis_result = None
                        async for chunk in llm_service.analyze_invoice_streaming(
                            invoice_text=invoice_text,
                            policy_text=policy_text,
                            employee_name=employee_name,
                        ):
                            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_ANALYSIS, data={**chunk['data'], 'filename': filename}).model_dump_json()}\n\n"

                            if chunk.get("data", {}).get("status") == "completed":
                                analysis_result = chunk["data"]["result"]

                        if not analysis_result:
                            raise ValueError("Analysis did not complete successfully")

                        progress.stage = "storing"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.VECTOR_STORAGE, data={'filename': filename, 'status': 'storing'}).model_dump_json()}\n\n"

                        await vector_store.store_invoice_analysis(
                            invoice_text=invoice_text,
                            analysis_result=analysis_result,
                            employee_name=employee_name,
                            invoice_filename=filename,
                            file_hash=invoice_hash,
                        )

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.VECTOR_STORAGE, data={'filename': filename, 'status': 'completed'}).model_dump_json()}\n\n"

                        result_data = {
                            "filename": filename,
                            "status": analysis_result.get("status"),
                            "reason": analysis_result.get("reason"),
                            "total_amount": analysis_result.get("total_amount"),
                            "reimbursement_amount": analysis_result.get(
                                "reimbursement_amount"
                            ),
                            "currency": analysis_result.get("currency"),
                            "categories": analysis_result.get("categories"),
                            "policy_violations": analysis_result.get(
                                "policy_violations"
                            ),
                            "from_cache": False,
                        }

                        analysis_results.append(result_data)

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.RESULT, data=result_data).model_dump_json()}\n\n"

                        progress.processed_invoices += 1
                        progress.stage = "completed"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                    except Exception as e:
                        logger.error(f"Error processing invoice {filename}: {e}")
                        error_data = {"file": filename, "error": str(e)}
                        processing_errors.append(error_data)

                        progress.failed_invoices += 1
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.ERROR, data=error_data).model_dump_json()}\n\n"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                completion_data = {
                    "success": True,
                    "message": f"Processed {len(analysis_results)} invoices successfully",
                    "employee_name": employee_name,
                    "total_invoices": total_invoices,
                    "processed_invoices": len(analysis_results),
                    "failed_invoices": len(processing_errors),
                    "results": analysis_results,
                    "processing_errors": processing_errors
                    if processing_errors
                    else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.DONE, data=completion_data).model_dump_json()}\n\n"

                logger.info(
                    f"Streaming invoice analysis completed for {employee_name}. "
                    f"Processed: {len(analysis_results)}, Failed: {len(processing_errors)}"
                )

        except Exception as e:
            logger.error(
                f"Unexpected error in streaming invoice analysis: {e}", exc_info=True
            )
            error_chunk = InvoiceAnalysisStreamingChunk(
                type=InvoiceAnalysisStreamingChunkType.ERROR,
                data={"error": f"Internal server error: {str(e)}"},
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_streaming_analysis(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        },
    )
