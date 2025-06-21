"""
File utility functions.

This module provides utilities for file handling, validation, and processing
including upload validation, ZIP file extraction, and file management.
"""

import hashlib
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import List

import aiofiles
from fastapi import HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


async def validate_file(file: UploadFile, allowed_extensions: List[str]) -> None:
    """
    Validate an uploaded file.

    Args:
        file: The uploaded file to validate
        allowed_extensions: List of allowed file extensions

    Raises:
        HTTPException: If file validation fails
    """
    if file.size and file.size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE}MB",
        )

    if file.filename:
        file_extension = Path(file.filename).suffix.lower().lstrip(".")
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}",
            )
    else:
        raise HTTPException(status_code=400, detail="Filename is required")

    if file.size == 0:
        raise HTTPException(status_code=400, detail="Empty files are not allowed")

    logger.info(f"File validation passed for: {file.filename}")


async def save_uploaded_file(file: UploadFile, destination_dir: str) -> str:
    """
    Save an uploaded file to the specified directory.

    Args:
        file: The uploaded file
        destination_dir: Directory to save the file in

    Returns:
        Path to the saved file

    Raises:
        HTTPException: If file saving fails
    """
    try:
        os.makedirs(destination_dir, exist_ok=True)

        safe_filename = sanitize_filename(file.filename or "unknown_file")
        file_path = os.path.join(destination_dir, safe_filename)

        logger.info(f"Attempting to save file: {file.filename} to {file_path}")

        if hasattr(file, "file") and hasattr(file.file, "read"):
            try:
                file.file.seek(0)
                content = file.file.read()

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)

                logger.info(f"File saved successfully (direct access): {file_path}")
                return file_path

            except Exception as direct_error:
                logger.warning(f"Direct file access failed: {direct_error}")

        # Fallback: Use FastAPI's async interface
        try:
            await file.seek(0)

            content = await file.read()

            if not content:
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} appears to be empty"
                )

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            logger.info(f"File saved successfully (async interface): {file_path}")
            return file_path

        except Exception as async_error:
            logger.error(f"Async file read failed: {async_error}")

            # Try chunk reading
            try:
                await file.seek(0)
                async with aiofiles.open(file_path, "wb") as f:
                    while True:
                        chunk = await file.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)

                logger.info(f"File saved successfully (chunked): {file_path}")
                return file_path

            except Exception as chunk_error:
                logger.error(f"All file read methods failed: {chunk_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read file {file.filename}: {str(chunk_error)}",
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove potentially dangerous characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    sanitized = filename

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "_")

    sanitized = sanitized.strip(" .")

    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


async def extract_zip_file(zip_path: str, extract_dir: str) -> List[str]:
    """
    Extract a ZIP file and return paths to extracted PDF files.

    Args:
        zip_path: Path to the ZIP file
        extract_dir: Directory to extract files to

    Returns:
        List of paths to extracted PDF files

    Raises:
        HTTPException: If extraction fails
    """
    try:
        pdf_files = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            file_list = zip_ref.namelist()

            pdf_file_names = [
                f
                for f in file_list
                if f.lower().endswith(".pdf") and not f.startswith("__MACOSX/")
            ]

            if not pdf_file_names:
                raise HTTPException(
                    status_code=400, detail="No PDF files found in the ZIP archive"
                )

            for pdf_name in pdf_file_names:
                try:
                    safe_name = sanitize_filename(os.path.basename(pdf_name))
                    extract_path = os.path.join(extract_dir, safe_name)

                    with (
                        zip_ref.open(pdf_name) as source,
                        open(extract_path, "wb") as target,
                    ):
                        target.write(source.read())

                    pdf_files.append(extract_path)
                    logger.debug(f"Extracted PDF: {pdf_name} -> {extract_path}")

                except Exception as e:
                    logger.warning(f"Error extracting {pdf_name}: {e}")
                    continue

        if not pdf_files:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract any PDF files from the ZIP archive",
            )

        logger.info(f"Successfully extracted {len(pdf_files)} PDF files from ZIP")
        return pdf_files

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file format")
    except Exception as e:
        logger.error(f"Error extracting ZIP file {zip_path}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to extract ZIP file: {str(e)}"
        )


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0


def delete_file_safe(file_path: str) -> bool:
    """
    Safely delete a file.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def create_temp_directory() -> str:
    """
    Create a temporary directory.

    Returns:
        Path to the created temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    logger.debug(f"Created temporary directory: {temp_dir}")
    return temp_dir


def cleanup_temp_directory(temp_dir: str) -> bool:
    """
    Clean up a temporary directory and all its contents.

    Args:
        temp_dir: Path to the temporary directory

    Returns:
        True if cleanup was successful, False otherwise
    """
    try:
        import shutil

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory {temp_dir}: {e}")
        return False


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.

    Args:
        filename: The filename

    Returns:
        File extension (without the dot)
    """
    return Path(filename).suffix.lower().lstrip(".")


def is_valid_pdf(file_path: str) -> bool:
    """
    Check if a file is a valid PDF.

    Args:
        file_path: Path to the file

    Returns:
        True if the file is a valid PDF, False otherwise
    """
    try:
        if get_file_extension(file_path) != "pdf":
            return False

        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception as e:
        logger.error(f"Error validating PDF {file_path}: {e}")
        return False


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory
    """
    try:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        raise


def get_upload_directory() -> str:
    """
    Get the configured upload directory path.

    Returns:
        Path to the upload directory
    """
    upload_dir = settings.UPLOAD_DIRECTORY
    ensure_directory_exists(upload_dir)
    return upload_dir


async def generate_file_hash(file_content: bytes) -> str:
    """
    Generate SHA-256 hash for file content.

    Args:
        file_content: Raw file content as bytes

    Returns:
        SHA-256 hash string
    """
    return hashlib.sha256(file_content).hexdigest()


async def generate_file_hash_from_path(file_path: str) -> str:
    """
    Generate SHA-256 hash for a file at given path.

    Args:
        file_path: Path to the file

    Returns:
        SHA-256 hash string
    """
    async with aiofiles.open(file_path, "rb") as f:
        content = await f.read()
        return await generate_file_hash(content)


async def generate_upload_file_hash(upload_file: UploadFile) -> str:
    """
    Generate SHA-256 hash for an UploadFile.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        SHA-256 hash string
    """
    content = await upload_file.read()
    await upload_file.seek(0)
    return await generate_file_hash(content)
