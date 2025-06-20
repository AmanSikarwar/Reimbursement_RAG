"""
Chatbot API Routes.

This module handles the RAG chatbot endpoint that allows users to query
processed invoice data using natural language.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    StreamingChunk,
    StreamingChunkType,
)
from app.services.chatbot_service import ChatbotService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for conversation history (in production, use a database)
conversation_store = {}


def get_vector_store(request: Request) -> VectorStoreService:
    """Dependency to get vector store service from app state."""
    return request.app.state.vector_store


@router.post("/chat", response_model=ChatResponse)
async def chat_with_invoices(
    request: Request,
    chat_request: ChatRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ChatResponse:
    """
    Chat with the invoice analysis system using natural language.

    This endpoint provides a RAG-based chatbot that can answer questions about
    processed invoices using vector search and LLM capabilities.

    Args:
        chat_request: The chat request containing query and session information
        vector_store: Vector store service dependency

    Returns:
        ChatResponse containing the bot's response and metadata

    Raises:
        HTTPException: If processing errors occur
    """
    logger.info(f"Processing chat query: {chat_request.query[:100]}...")

    try:
        # Initialize services
        llm_service = LLMService()
        chatbot_service = ChatbotService(vector_store, llm_service)

        # Get or create conversation history
        session_id = chat_request.session_id or "default"
        conversation_history = conversation_store.get(session_id, [])

        # Process the query
        response = await chatbot_service.process_query(
            query=chat_request.query,
            conversation_history=conversation_history,
            filters=chat_request.filters,
        )

        # Update conversation history
        conversation_history.append(
            ChatMessage(
                role="user", content=chat_request.query, timestamp=datetime.utcnow()
            )
        )
        conversation_history.append(
            ChatMessage(
                role="assistant",
                content=response["response"],
                timestamp=datetime.utcnow(),
            )
        )

        # Keep only recent messages (limit memory usage)
        max_history = 20  # Keep last 10 exchanges
        if len(conversation_history) > max_history:
            conversation_history = conversation_history[-max_history:]

        conversation_store[session_id] = conversation_history

        # Prepare response
        chat_response = ChatResponse(
            response=response["response"],
            session_id=session_id,
            sources=response.get("sources", []),
            retrieved_documents=response.get("retrieved_documents", 0),
            query_type=response.get("query_type", "general"),
            confidence_score=response.get("confidence_score", 0.8),
            suggestions=response.get("suggestions", []),
            timestamp=datetime.utcnow(),
        )

        logger.info(f"Chat response generated successfully for session: {session_id}")
        return chat_response

    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing chat query: {str(e)}"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str) -> List[ChatMessage]:
    """
    Get conversation history for a specific session.

    Args:
        session_id: The session identifier

    Returns:
        List of chat messages for the session
    """
    history = conversation_store.get(session_id, [])
    return history


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str) -> dict:
    """
    Clear conversation history for a specific session.

    Args:
        session_id: The session identifier

    Returns:
        Confirmation message
    """
    if session_id in conversation_store:
        del conversation_store[session_id]
        logger.info(f"Cleared chat history for session: {session_id}")

    return {
        "message": f"Chat history cleared for session: {session_id}",
        "timestamp": datetime.utcnow(),
    }


@router.get("/chat/sessions")
async def get_active_sessions() -> dict:
    """
    Get list of active chat sessions.

    Returns:
        Dictionary containing active session information
    """
    sessions = list(conversation_store.keys())
    return {
        "active_sessions": sessions,
        "total_sessions": len(sessions),
        "timestamp": datetime.utcnow(),
    }


@router.post("/chat/stream")
async def chat_with_invoices_streaming(
    request: Request,
    chat_request: ChatStreamRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """
    Stream chat responses with the invoice analysis system using natural language.

    This endpoint provides a RAG-based chatbot that streams answers about
    processed invoices using vector search and LLM capabilities.

    Args:
        chat_request: The chat request containing query and session information
        vector_store: Vector store service dependency

    Returns:
        Streaming response with chunks of data using Server-Sent Events (SSE)

    Raises:
        HTTPException: If processing errors occur
    """
    logger.info(f"Processing streaming chat query: {chat_request.query[:100]}...")

    async def generate_streaming_response():
        """Generate streaming response chunks with optimized SSE format."""
        try:
            # Initialize services
            llm_service = LLMService()
            chatbot_service = ChatbotService(vector_store, llm_service)

            # Get or create conversation history
            session_id = chat_request.session_id or "default"
            conversation_history = conversation_store.get(session_id, [])

            # Process the streaming query
            async for chunk in chatbot_service.process_query_streaming(
                query=chat_request.query,
                conversation_history=conversation_history,
                filters=chat_request.filters,
            ):
                # Create streaming chunk with timestamp
                streaming_chunk = StreamingChunk(
                    type=StreamingChunkType(chunk["type"]),
                    data=chunk["data"],
                    timestamp=datetime.utcnow(),
                )

                # Yield the chunk as SSE format with proper formatting
                chunk_json = streaming_chunk.model_dump_json()
                yield f"data: {chunk_json}\n\n"

                # Add small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            # Update conversation history for non-error responses
            if chat_request.session_id:
                conversation_history.append(
                    ChatMessage(
                        role="user",
                        content=chat_request.query,
                        timestamp=datetime.utcnow(),
                    )
                )
                conversation_history.append(
                    ChatMessage(
                        role="assistant",
                        content="[Streaming response completed]",
                        timestamp=datetime.utcnow(),
                    )
                )

                # Keep only recent messages (limit memory usage)
                max_history = 20
                if len(conversation_history) > max_history:
                    conversation_history = conversation_history[-max_history:]

                conversation_store[session_id] = conversation_history

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            error_chunk = StreamingChunk(
                type=StreamingChunkType.ERROR,
                data=f"Error processing chat query: {str(e)}",
                timestamp=datetime.utcnow(),
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate_streaming_response(),
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
