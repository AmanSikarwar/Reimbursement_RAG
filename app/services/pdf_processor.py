"""
PDF Processing Service.

This service handles PDF text extraction and processing for both
invoice documents and HR policy documents.
"""

import asyncio
import logging
from pathlib import Path

import PyPDF2

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Service for processing PDF documents and extracting text content.

    This class provides methods to extract text from PDF files with error handling
    and support for various PDF formats.
    """

    def __init__(self):
        """Initialize the PDF processor."""
        self.logger = logger

    async def extract_text(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If text extraction fails
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._extract_text_sync, pdf_path
            )
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _extract_text_sync(self, pdf_path: str) -> str:
        """
        Synchronous text extraction from PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text_content = []

        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                if pdf_reader.is_encrypted:
                    self.logger.warning(
                        f"PDF {pdf_path} is encrypted, attempting to decrypt"
                    )
                    if not pdf_reader.decrypt(""):
                        raise ValueError("PDF is encrypted and cannot be read")

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(page_text)
                            self.logger.debug(
                                f"Extracted text from page {page_num + 1}"
                            )
                    except Exception as e:
                        self.logger.warning(
                            f"Error extracting text from page {page_num + 1}: {e}"
                        )
                        continue

        except Exception as e:
            self.logger.error(f"Error reading PDF file {pdf_path}: {e}")
            raise ValueError(f"Cannot read PDF file: {str(e)}")

        if not text_content:
            raise ValueError("No text content could be extracted from the PDF")

        extracted_text = "\n\n".join(text_content)
        self.logger.info(
            f"Successfully extracted {len(extracted_text)} characters from {pdf_path}"
        )

        return extracted_text

    async def extract_metadata(self, pdf_path: str) -> dict:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._extract_metadata_sync, pdf_path
            )
        except Exception as e:
            self.logger.error(f"Error extracting metadata from PDF {pdf_path}: {e}")
            return {}

    def _extract_metadata_sync(self, pdf_path: str) -> dict:
        """
        Synchronous metadata extraction from PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                metadata = {
                    "num_pages": len(pdf_reader.pages),
                    "is_encrypted": pdf_reader.is_encrypted,
                }

                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    metadata.update(
                        {
                            "title": getattr(info, "title", None),
                            "author": getattr(info, "author", None),
                            "subject": getattr(info, "subject", None),
                            "creator": getattr(info, "creator", None),
                            "producer": getattr(info, "producer", None),
                            "creation_date": getattr(info, "creation_date", None),
                            "modification_date": getattr(
                                info, "modification_date", None
                            ),
                        }
                    )

                return metadata

        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            return {"error": str(e)}

    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate if a file is a valid PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    _ = pdf_reader.pages[0]
                return True
        except Exception as e:
            self.logger.error(f"PDF validation failed for {pdf_path}: {e}")
            return False

    async def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages in the PDF
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._get_page_count_sync, pdf_path
            )
        except Exception as e:
            self.logger.error(f"Error getting page count from PDF {pdf_path}: {e}")
            return 0

    def _get_page_count_sync(self, pdf_path: str) -> int:
        """
        Synchronous page count extraction.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages in the PDF
        """
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            self.logger.error(f"Error getting page count from {pdf_path}: {e}")
            return 0
