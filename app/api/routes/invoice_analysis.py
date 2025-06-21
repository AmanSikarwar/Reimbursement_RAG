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
    sanitize_filename,
    save_uploaded_file,
    validate_file,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_vector_store(request: Request) -> VectorStoreService:
    """Dependency to get vector store service from app state."""
    return request.app.state.vector_store


@router.post("/analyze-invoices", response_model=InvoiceAnalysisResponse)
async def analyze_invoices(
    request: Request,
    employee_name: str = Form(..., description="Name of the employee"),
    policy_file: UploadFile = File(..., description="HR reimbursement policy PDF"),
    invoices_zip: UploadFile = File(
        ..., description="ZIP file containing invoice PDFs"
    ),
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> InvoiceAnalysisResponse:
    """
    Analyze employee invoices against HR reimbursement policy.

    This endpoint processes a ZIP file containing invoice PDFs and analyzes them
    against the provided HR policy using an LLM. Results are stored in the vector database.

    Args:
        employee_name: Name of the employee submitting invoices
        policy_file: PDF file containing HR reimbursement policy
        invoices_zip: ZIP file containing one or more invoice PDFs
        vector_store: Vector store service dependency

    Returns:
        InvoiceAnalysisResponse with processing results

    Raises:
        HTTPException: If file validation fails or processing errors occur
    """
    logger.info(f"Starting invoice analysis for employee: {employee_name}")

    try:
        # Validate uploaded files
        await validate_file(policy_file, ["pdf"])
        await validate_file(invoices_zip, ["zip"])

        # Initialize services
        pdf_processor = PDFProcessor()
        llm_service = LLMService()

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save and process policy file
            policy_path = await save_uploaded_file(policy_file, temp_dir)
            policy_text = await pdf_processor.extract_text(policy_path)

            if not policy_text.strip():
                raise HTTPException(
                    status_code=400, detail="Could not extract text from policy PDF"
                )

            # Store policy document in vector database for chatbot context
            try:
                await vector_store.store_policy_document(
                    policy_text=policy_text,
                    policy_name=f"HR_Policy_{employee_name}_{datetime.now().strftime('%Y%m%d')}",
                    organization="Company",
                )
                logger.info(
                    f"Policy document stored in vector database for {employee_name}"
                )
            except Exception as e:
                logger.warning(f"Failed to store policy in vector database: {e}")
                # Don't fail the entire process if policy storage fails

            # Save and extract invoices ZIP file
            zip_path = await save_uploaded_file(invoices_zip, temp_dir)
            invoice_files = await extract_zip_file(zip_path, temp_dir)

            if not invoice_files:
                raise HTTPException(
                    status_code=400, detail="No PDF files found in the ZIP archive"
                )

            # Process each invoice
            analysis_results = []
            processing_errors = []

            # Process invoices concurrently (with limit to avoid overwhelming the system)
            semaphore = asyncio.Semaphore(3)  # Limit concurrent processing

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

            # Process all invoices
            tasks = [
                process_single_invoice(invoice_path) for invoice_path in invoice_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect successful results
            for result in results:
                if result and not isinstance(result, Exception):
                    analysis_results.append(result)

            # Prepare response
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
    # Extract text from invoice
    invoice_text = await pdf_processor.extract_text(invoice_path)

    if not invoice_text.strip():
        raise ValueError("Could not extract text from invoice PDF")

    # Analyze invoice with LLM
    analysis_result = await llm_service.analyze_invoice(
        invoice_text=invoice_text, policy_text=policy_text, employee_name=employee_name
    )

    # Store in vector database
    await vector_store.store_invoice_analysis(
        invoice_text=invoice_text,
        analysis_result=analysis_result,
        employee_name=employee_name,
        invoice_filename=os.path.basename(invoice_path),
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


@router.post("/analyze-invoices-stream")
async def analyze_invoices_streaming(
    request: Request,
    employee_name: str = Form(..., description="Name of the employee"),
    policy_file: UploadFile = File(..., description="HR reimbursement policy PDF"),
    invoices_zip: UploadFile = File(
        ..., description="ZIP file containing invoice PDFs"
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

    # Read file contents BEFORE entering the async generator to avoid I/O issues
    try:
        # Validate files first
        await validate_file(policy_file, ["pdf"])
        await validate_file(invoices_zip, ["zip"])

        logger.info(
            f"Reading file contents for: {policy_file.filename}, {invoices_zip.filename}"
        )

        # Read file contents immediately
        policy_content = await policy_file.read()
        zip_content = await invoices_zip.read()

        logger.info(
            f"Successfully read file contents: policy={len(policy_content)} bytes, zip={len(zip_content)} bytes"
        )

        # Store file metadata for use in generator
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
            # Yield initial metadata
            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.METADATA, data={'employee': employee_name, 'status': 'starting'}).model_dump_json()}\n\n"

            # Initialize services
            pdf_processor = PDFProcessor()
            llm_service = LLMService()

            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Process policy file
                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'extracting_policy'}).model_dump_json()}\n\n"

                # Save policy file using pre-read content
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

                # Store policy document in vector database for chatbot context
                try:
                    await vector_store.store_policy_document(
                        policy_text=policy_text,
                        policy_name=f"HR_Policy_{employee_name}_{datetime.now().strftime('%Y%m%d')}",
                        organization="Company",
                    )
                    logger.info(
                        f"Policy document stored in vector database for {employee_name}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to store policy in vector database: {e}")
                    # Don't fail the entire process if policy storage fails

                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.POLICY_PROCESSING, data={'status': 'completed', 'policy_length': len(policy_text)}).model_dump_json()}\n\n"

                # Extract invoice files - save ZIP using pre-read content
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

                # Yield initial progress
                progress = InvoiceAnalysisProgress(
                    current_invoice=0,
                    total_invoices=total_invoices,
                    processed_invoices=0,
                    failed_invoices=0,
                    current_filename=None,
                    stage="starting",
                )
                yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                # Process each invoice with streaming
                for idx, invoice_path in enumerate(invoice_files, 1):
                    filename = os.path.basename(invoice_path)

                    try:
                        # Update progress
                        progress.current_invoice = idx
                        progress.current_filename = filename
                        progress.stage = "extracting_text"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        # Extract invoice text
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_EXTRACTION, data={'filename': filename, 'status': 'extracting'}).model_dump_json()}\n\n"

                        invoice_text = await pdf_processor.extract_text(invoice_path)

                        if not invoice_text.strip():
                            raise ValueError("Could not extract text from invoice PDF")

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_EXTRACTION, data={'filename': filename, 'status': 'completed', 'text_length': len(invoice_text)}).model_dump_json()}\n\n"

                        # Update progress
                        progress.stage = "analyzing"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        # Analyze invoice with streaming
                        analysis_result = None
                        async for chunk in llm_service.analyze_invoice_streaming(
                            invoice_text=invoice_text,
                            policy_text=policy_text,
                            employee_name=employee_name,
                        ):
                            # Forward LLM streaming chunks
                            yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.INVOICE_ANALYSIS, data={**chunk['data'], 'filename': filename}).model_dump_json()}\n\n"

                            # Check if analysis is completed
                            if chunk.get("data", {}).get("status") == "completed":
                                analysis_result = chunk["data"]["result"]

                        if not analysis_result:
                            raise ValueError("Analysis did not complete successfully")

                        # Update progress
                        progress.stage = "storing"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                        # Store in vector database
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.VECTOR_STORAGE, data={'filename': filename, 'status': 'storing'}).model_dump_json()}\n\n"

                        await vector_store.store_invoice_analysis(
                            invoice_text=invoice_text,
                            analysis_result=analysis_result,
                            employee_name=employee_name,
                            invoice_filename=filename,
                        )

                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.VECTOR_STORAGE, data={'filename': filename, 'status': 'completed'}).model_dump_json()}\n\n"

                        # Prepare result
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
                        }

                        analysis_results.append(result_data)

                        # Yield individual result
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.RESULT, data=result_data).model_dump_json()}\n\n"

                        # Update progress
                        progress.processed_invoices += 1
                        progress.stage = "completed"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                    except Exception as e:
                        logger.error(f"Error processing invoice {filename}: {e}")
                        error_data = {"file": filename, "error": str(e)}
                        processing_errors.append(error_data)

                        # Update progress
                        progress.failed_invoices += 1
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.ERROR, data=error_data).model_dump_json()}\n\n"
                        yield f"data: {InvoiceAnalysisStreamingChunk(type=InvoiceAnalysisStreamingChunkType.PROGRESS, data=progress.model_dump()).model_dump_json()}\n\n"

                # Yield final completion
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
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Transfer-Encoding": "chunked",  # Enable chunked transfer
        },
    )
