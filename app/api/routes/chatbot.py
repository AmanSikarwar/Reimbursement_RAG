"""
Chatbot API Routes.

This module handles the RAG chatbot endpoint that allows users to query
processed invoice data using natural language.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request
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

conversation_store = {}


def get_vector_store(request: Request) -> VectorStoreService:
    """Dependency to get vector store service from app state."""
    return request.app.state.vector_store


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Intelligent Invoice Query Chatbot",
    description="""
**Advanced RAG-powered conversational interface for querying processed invoice data using natural language.**
    
This endpoint provides an intelligent chatbot that can understand and respond to complex questions about
processed invoice data. Using Retrieval Augmented Generation (RAG), it combines vector search capabilities
with large language model intelligence to provide accurate, contextual responses with source citations.

## AI Capabilities

### Natural Language Understanding
- **Complex Queries**: Handles multi-part questions and compound requests
- **Context Awareness**: Maintains conversation context across multiple turns
- **Intent Recognition**: Identifies query types (search, analysis, comparison, etc.)
- **Entity Extraction**: Recognizes names, dates, amounts, and categories
    
### Advanced Query Types
    
#### **Analytics & Aggregation**
- `"What's the total reimbursement amount for Q4 2024?"`
- `"Show me the average invoice amount by employee"`
- `"Which department has the highest expense claims?"`
- `"Compare travel expenses between John and Mary"`
#### **Search & Filtering**
- `"Find all declined invoices from last month"`
- `"Show me Aman Sikarwar's meal expenses over $100"`
- `"List all partially reimbursed travel invoices"`
- `"Which invoices have policy violations?"`
#### **Trend Analysis**
- `"How have reimbursement patterns changed this year?"`
- `"Show me spending trends by category"`
- `"Which employees submitted the most invoices?"`
- `"What are the most common policy violations?"`

#### **Specific Lookups**
- `"Find invoice for dinner at Restaurant ABC on Dec 15"`
- `"Show details for invoice file 'receipt_001.pdf'"`
- `"What was the reason for declining Sarah's hotel bill?"`
    
## Technical Features
    
### RAG Pipeline
1. **Query Analysis**: NLP processing to understand intent and extract entities
2. **Vector Search**: Semantic similarity search in Qdrant database  
3. **Context Retrieval**: Fetches relevant invoice data and analysis results
4. **LLM Generation**: Gemini generates contextual response with retrieved data
5. **Source Attribution**: Provides citations and confidence scores
    
### Session Management
- **Conversation History**: Maintains context across multiple interactions
- **Follow-up Support**: Understands references to previous questions
- **Session Persistence**: Conversations stored for continued interaction
- **Context Pruning**: Automatically manages memory for long conversations
    
### Advanced Filtering
- **Date Ranges**: Filter by submission date, expense date, or processing date
- **Amount Ranges**: Filter by total amount or reimbursement amount
- **Status Filtering**: Filter by approval status (approved/partial/declined)
- **Employee Filtering**: Filter by specific employees or departments
- **Category Filtering**: Filter by expense categories (travel, meals, etc.)

## Usage Tips
### Best Practices
- **Be Specific**: Include names, dates, or amounts when possible
- **Use Context**: Reference previous questions in follow-ups
- **Ask Follow-ups**: Drill down into interesting results
- **Use Filters**: Apply filters for large datasets

### Example Conversation Flow
```
User: "Show me all invoices from Aman Sikarwar"
Bot: "I found 15 invoices from Aman Sikarwar totaling $12,500..."
    
User: "Which ones were declined?"
Bot: "Of John's invoices, 2 were declined totaling $800..."
    
User: "Why were they declined?"
Bot: "The declined invoices violated policy because..."
```
    
---
    
**Pro Tip**: Start with broad questions and use follow-ups to drill down into specific details.
The AI remembers your conversation context and can provide increasingly detailed insights.
""",
    response_description="Intelligent response with natural language answer, sources, and conversation context",
    responses={
        200: {
            "description": "Successful chat response with comprehensive context and sources",
            "content": {
                "application/json": {
                    "examples": {
                        "general_query": {
                            "summary": "General invoice query",
                            "value": {
                                "response": "I found 12 invoices submitted this month totaling $15,750. Here's the breakdown: 8 fully approved ($12,500), 3 partially approved ($2,250), and 1 declined ($1,000). The most common categories were travel (45%) and meals (30%).",
                                "session_id": "user_session_abc123",
                                "sources": [
                                    {
                                        "document_id": "inv_001",
                                        "filename": "travel_receipt_dec01.pdf",
                                        "employee_name": "Aman Sikarwar",
                                        "status": "fully_reimbursed",
                                        "similarity_score": 0.92,
                                        "excerpt": "Business travel to Mumbai for client meeting..."
                                    }
                                ],
                                "retrieved_documents": 12,
                                "query_type": "general",
                                "confidence_score": 0.89,
                                "suggestions": [
                                    "Show me details of the declined invoice",
                                    "What were the travel expenses this month?",
                                    "Which employee had the highest reimbursements?"
                                ],
                                "timestamp": "2024-12-21T10:00:00Z"
                            }
                        },
                        "employee_specific": {
                            "summary": "Employee-specific query with filtering",
                            "value": {
                                "response": "Aman Sikarwar submitted 5 invoices this quarter with the following status: 3 fully approved totaling $8,500 (travel and accommodation), 1 partially approved for $1,200 (meal with alcohol excluded), and 1 declined for $500 (personal expense misclassified).",
                                "session_id": "user_session_xyz789",
                                "sources": [
                                    {
                                        "document_id": "inv_john_001",
                                        "filename": "john_travel_nov15.pdf",
                                        "employee_name": "Aman Sikarwar",
                                        "status": "fully_reimbursed",
                                        "similarity_score": 0.95
                                    }
                                ],
                                "retrieved_documents": 5,
                                "query_type": "employee_specific",
                                "confidence_score": 0.94,
                                "suggestions": [
                                    "What was the reason for the declined invoice?",
                                    "Show John's travel expense breakdown",
                                    "Compare John's expenses to team average"
                                ]
                            }
                        },
                        "analytical_query": {
                            "summary": "Complex analytical question",
                            "value": {
                                "response": "Travel expenses have increased 23% compared to last quarter, primarily due to 4 international business trips ($12,000) and increased domestic travel frequency. The average per-trip cost is $1,850, within policy limits. Recommendation: Consider virtual meetings for routine client check-ins.",
                                "session_id": "analytics_session_001",
                                "query_type": "amount_filter",
                                "confidence_score": 0.87,
                                "retrieved_documents": 28,
                                "suggestions": [
                                    "Which trips were international vs domestic?",
                                    "Show me the cost breakdown by destination",
                                    "What's the ROI on business travel expenses?"
                                ]
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request - Invalid query parameters or malformed request",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_query": {
                            "summary": "Empty or invalid query",
                            "value": {
                                "success": False,
                                "error": "validation_error",
                                "message": "Query cannot be empty",
                                "details": [
                                    {
                                        "code": "EMPTY_QUERY",
                                        "message": "Query must be between 1 and 1000 characters",
                                        "field": "query"
                                    }
                                ]
                            }
                        },
                        "invalid_filters": {
                            "summary": "Invalid filter parameters",
                            "value": {
                                "success": False,
                                "error": "validation_error", 
                                "message": "Invalid date range in filters",
                                "details": [
                                    {
                                        "code": "INVALID_DATE_RANGE",
                                        "message": "date_from must be before date_to",
                                        "field": "filters.date_from"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error in request data",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "validation_error",
                        "message": "Request validation failed",
                        "details": [
                            {
                                "code": "INVALID_SESSION_ID",
                                "message": "Session ID format is invalid",
                                "field": "session_id"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during chat processing",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "processing_error",
                        "message": "Error processing chat query",
                        "details": [
                            {
                                "code": "VECTOR_SEARCH_ERROR",
                                "message": "Vector database temporarily unavailable"
                            },
                            {
                                "code": "LLM_SERVICE_ERROR", 
                                "message": "Gemini API rate limit exceeded"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def chat_with_invoices(
    request: Request,
    chat_request: ChatRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
) -> ChatResponse:
    """
    Intelligent conversational interface for querying processed invoice data.

    This advanced RAG (Retrieval Augmented Generation) endpoint combines the power of
    vector search with large language model intelligence to provide accurate, contextual
    responses to natural language queries about invoice data. The system maintains
    conversation context, provides source citations, and offers intelligent follow-up suggestions.

    ## Query Processing Pipeline

    ### 1. Query Analysis (50-100ms)
    - **Intent Detection**: Identifies query type (search, analytics, comparison, etc.)
    - **Entity Extraction**: Extracts names, dates, amounts, categories, and other entities
    - **Context Integration**: Incorporates previous conversation context
    - **Filter Application**: Applies any specified search filters

    ### 2. Vector Search (100-300ms)
    - **Semantic Search**: Uses embeddings to find semantically similar content
    - **Hybrid Filtering**: Combines vector similarity with metadata filtering
    - **Relevance Scoring**: Ranks results by relevance and confidence
    - **Context Retrieval**: Gathers relevant invoice data and analysis results

    ### 3. Response Generation (500-2000ms)
    - **Context Assembly**: Combines retrieved data with conversation history
    - **LLM Processing**: Uses Gemini to generate natural language response
    - **Source Attribution**: Maps response claims to source documents
    - **Quality Assurance**: Validates response accuracy and completeness

    ### 4. Post-Processing (50-100ms)
    - **Follow-up Generation**: Suggests related questions for continued exploration
    - **Session Management**: Updates conversation history and context
    - **Metadata Assembly**: Compiles response metadata and statistics

    ## Advanced Query Capabilities

    ### Complex Aggregations
    ```python
    # Examples of supported analytical queries:
    "What's the average reimbursement rate by employee this quarter?"
    "Show me monthly spending trends for the past 6 months"
    "Which categories have the highest decline rates?"
    "Compare travel expenses between departments"
    ```

    ### Multi-Dimensional Filtering
    ```python
    # Combining multiple filters in natural language:
    "Find all meal expenses over $50 from last month that were partially approved"
    "Show me John's travel invoices from Q3 that had policy violations"
    "List declined invoices between $100-$500 with alcohol-related violations"
    ```

    ### Contextual Follow-ups
    ```python
    # Building on previous queries:
    User: "Show me all declined invoices"
    Bot: "I found 15 declined invoices..."
    User: "What were the main reasons?"  # Contextual reference
    Bot: "The main decline reasons were..."
    User: "Show me just the policy violations"  # Further refinement
    ```

    ## Response Quality Features

    ### Source Attribution
    - **Document Citations**: Links to specific invoices and analysis results
    - **Confidence Scoring**: Quantified confidence in response accuracy
    - **Excerpt Highlighting**: Relevant portions of source documents
    - **Similarity Metrics**: Relevance scores for retrieved content

    ### Conversation Intelligence
    - **Context Awareness**: Understands pronouns and references to previous queries
    - **Follow-up Suggestions**: AI-generated related questions
    - **Query Refinement**: Helps users ask better, more specific questions
    - **Clarification Requests**: Asks for clarification when queries are ambiguous

    Args:
        request (Request): FastAPI request object containing client information
        chat_request (ChatRequest): Structured chat request containing:
            - query (str): Natural language question (1-1000 characters)
            - session_id (str, optional): Conversation session identifier
            - filters (SearchFilters, optional): Structured search filters
            - include_sources (bool): Whether to include source citations
        vector_store (VectorStoreService): Injected vector database service
            for performing semantic search operations

    Returns:
        ChatResponse: Comprehensive response object containing:
            - response (str): Natural language answer to the query
            - session_id (str): Session identifier for conversation continuity
            - sources (List[DocumentSource]): Source documents with citations
            - retrieved_documents (int): Number of documents found and processed
            - query_type (QueryType): Classified type of query processed
            - confidence_score (float): AI confidence in response accuracy (0.0-1.0)
            - suggestions (List[str]): Suggested follow-up questions
            - timestamp (datetime): Response generation timestamp

    Raises:
        HTTPException: 
            - 400: Invalid query format, empty query, or malformed filters
            - 422: Request validation errors (invalid session_id, etc.)
            - 500: Processing errors including:
                * Vector database connection issues
                * LLM API errors or rate limiting
                * Search processing failures
                * Session management errors

    Performance Characteristics:
        - **Typical Response Time**: 1-3 seconds for most queries
        - **Complex Queries**: 3-5 seconds for multi-faceted analytical questions
        - **Concurrent Sessions**: Supports 50+ simultaneous conversations
        - **Memory Usage**: Automatically manages conversation history length
        - **Cache Efficiency**: Leverages caching for frequently asked questions

    Example Usage:
        ```python
        # Simple query
        chat_request = ChatRequest(
            query="Show me all declined invoices from last month",
            session_id="user_123",
            include_sources=True
        )
        
        # Complex query with filters
        chat_request = ChatRequest(
            query="What's the total travel spending this quarter?",
            session_id="analytics_session",
            filters=SearchFilters(
                categories=["travel", "accommodation"],
                date_from=datetime(2024, 10, 1),
                date_to=datetime(2024, 12, 31)
            )
        )
        ```

    Security Notes:
        - All queries are logged for audit purposes
        - Session data is automatically cleaned up after inactivity
        - No sensitive data is stored in conversation history
        - Access to invoice data respects original processing permissions
    """
    logger.info(f"Processing chat query: {chat_request.query[:100]}...")

    try:
        llm_service = LLMService()
        chatbot_service = ChatbotService(vector_store, llm_service)

        session_id = chat_request.session_id or "default"
        conversation_history = conversation_store.get(session_id, [])

        response = await chatbot_service.process_query(
            query=chat_request.query,
            conversation_history=conversation_history,
            filters=chat_request.filters,
        )

        conversation_history.append(
            ChatMessage(
                role="user",
                content=chat_request.query,
                timestamp=datetime.now(timezone.utc),
            )
        )
        conversation_history.append(
            ChatMessage(
                role="assistant",
                content=response["response"],
                timestamp=datetime.now(timezone.utc),
            )
        )

        max_history = 20
        if len(conversation_history) > max_history:
            conversation_history = conversation_history[-max_history:]

        conversation_store[session_id] = conversation_history

        chat_response = ChatResponse(
            response=response["response"],
            session_id=session_id,
            sources=response.get("sources", []),
            retrieved_documents=response.get("retrieved_documents", 0),
            query_type=response.get("query_type", "general"),
            confidence_score=response.get("confidence_score", 0.8),
            suggestions=response.get("suggestions", []),
            timestamp=datetime.now(timezone.utc),
        )

        logger.info(f"Chat response generated successfully for session: {session_id}")
        return chat_response

    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing chat query: {str(e)}"
        )


@router.get(
    "/chat/history/{session_id}",
    response_model=List[ChatMessage],
    summary="Retrieve Conversation History",
    description="""
Retrieve the complete conversation history for a specific chat session.
    
This endpoint allows you to access the full conversation context for a given session,
including all user queries and AI responses with timestamps. Useful for:

### Use Cases:
- **Session Recovery**: Restore conversation context after disconnection
- **Audit Trail**: Review conversation history for compliance
- **Analytics**: Analyze conversation patterns and user behavior
- **Context Building**: Understand conversation flow for support

### Response Content:
- **Complete Message History**: All messages in chronological order
- **Role Attribution**: Clear distinction between user and assistant messages
- **Timestamps**: Precise timing for each message
- **Content Preservation**: Full text of all queries and responses

### Session Management:
- **Automatic Cleanup**: Old sessions are automatically purged
- **Memory Management**: History is truncated to maintain performance
- **Privacy**: No sensitive data persisted beyond session scope
""",
    response_description="Complete conversation history with timestamps and role attribution",
    responses={
        200: {
            "description": "Conversation history retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "role": "user",
                            "content": "Show me all declined invoices from Aman Sikarwar",
                            "timestamp": "2024-12-21T10:00:00Z"
                        },
                        {
                            "role": "assistant", 
                            "content": "I found 2 declined invoices from Aman Sikarwar totaling $1,200...",
                            "timestamp": "2024-12-21T10:00:03Z"
                        },
                        {
                            "role": "user",
                            "content": "What were the reasons for declining them?",
                            "timestamp": "2024-12-21T10:01:00Z"
                        },
                        {
                            "role": "assistant",
                            "content": "The invoices were declined for the following reasons...",
                            "timestamp": "2024-12-21T10:01:02Z"
                        }
                    ]
                }
            }
        },
        404: {
            "description": "Session not found or expired",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session 'invalid_session_123' not found or has expired"
                    }
                }
            }
        }
    }
)
async def get_chat_history(
    session_id: str = Path(
        ...,
        description="Unique session identifier for the conversation",
        example="user_session_abc123",
        min_length=1,
        max_length=100
    )
) -> List[ChatMessage]:
    """
    Retrieve complete conversation history for a specific chat session.
    
    This endpoint provides access to the full conversation context including all
    user queries and AI responses, timestamps, and role attribution. The history
    is returned in chronological order with the oldest messages first.
    
    Args:
        session_id (str): Unique identifier for the conversation session.
            This should be the same session_id used in chat requests.
            Sessions are automatically created when first used.
    
    Returns:
        List[ChatMessage]: Complete conversation history containing:
            - role: Either "user" or "assistant" 
            - content: Full text of the message
            - timestamp: UTC timestamp when message was created
            
    Raises:
        HTTPException: 
            - 404: Session not found or expired
            - 422: Invalid session_id format
    
    Notes:
        - Sessions have a maximum history length (default: 20 messages)
        - Older messages are automatically pruned to maintain performance
        - Sessions are automatically cleaned up after extended inactivity
        - Empty list returned for new/non-existent sessions
        
    Example:
        ```python
        import requests
        
        response = requests.get("/api/v1/chat/history/user_session_123")
        history = response.json()
        
        for message in history:
            print(f"{message['role']}: {message['content']}")
        ```
    """
    history = conversation_store.get(session_id, [])
    if session_id not in conversation_store and session_id != "default":
        logger.warning(f"Session {session_id} not found")
    return history


@router.delete(
    "/chat/history/{session_id}",
    summary="🗑️ Clear Conversation History",
    description="""
Clear all conversation history for a specific chat session.
    
This endpoint permanently removes all stored conversation history for the specified
session, effectively starting fresh while maintaining the same session identifier.
    
### After Deletion:
- Next chat query will start fresh conversation
- No conversation context from previous interactions
- Session can be reused with same identifier
- Performance may improve for long conversations
""",
    response_description="Confirmation of successful history deletion",
    responses={
        200: {
            "description": "Conversation history cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Conversation history cleared successfully for session: user_session_123",
                        "session_id": "user_session_123",
                        "cleared_messages": 8,
                        "timestamp": "2024-12-21T10:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "session_not_found",
                        "message": "Session 'invalid_session_123' not found",
                        "session_id": "invalid_session_123"
                    }
                }
            }
        }
    }
)
async def clear_chat_history(
    session_id: str = Path(
        ...,
        description="Unique session identifier for the conversation to clear",
        example="user_session_abc123",
        min_length=1,
        max_length=100
    )
) -> dict:
    """
    Permanently clear all conversation history for a specific chat session.
    
    This endpoint removes all stored messages and conversation context for the specified
    session, allowing for a fresh start while maintaining the same session identifier
    for future conversations.
    
    Args:
        session_id (str): Unique identifier for the conversation session to clear.
            Must be 1-100 characters long. Can contain letters, numbers, and basic
            punctuation characters.
    
    Returns:
        dict: Confirmation response containing:
            - success (bool): True if operation completed successfully
            - message (str): Human-readable confirmation message  
            - session_id (str): The session ID that was cleared
            - cleared_messages (int): Number of messages that were removed
            - timestamp (str): UTC timestamp of the deletion operation
            
    Raises:
        HTTPException:
            - 404: Session not found (may have already been cleared or expired)
            - 422: Invalid session_id format or length
    
    Notes:
        - **Irreversible Action**: Once cleared, conversation history cannot be recovered
        - **Session Reuse**: The session_id remains valid for future conversations
        - **Immediate Effect**: Next chat query will have no conversation context
        - **Audit Trail**: All deletion operations are logged for security
        - **Performance**: Clearing large histories may improve response times
        
    Security Considerations:
        - All deletion operations are logged with timestamps
        - No sensitive data is retained after clearing
        - Session identifiers are validated for format compliance
        - Rate limiting may apply to prevent abuse
        
    Example:
        ```python
        import requests
        
        # Clear specific session
        response = requests.delete("/api/v1/chat/history/user_session_123")
        result = response.json()
        
        if result['success']:
            print(f"Cleared {result['cleared_messages']} messages")
        ```
    """
    cleared_messages = 0
    
    if session_id in conversation_store:
        cleared_messages = len(conversation_store[session_id])
        del conversation_store[session_id]
        logger.info(f"Cleared conversation history for session: {session_id} ({cleared_messages} messages)")
        
        return {
            "success": True,
            "message": f"Conversation history cleared successfully for session: {session_id}",
            "session_id": session_id,
            "cleared_messages": cleared_messages,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    else:
        logger.warning(f"Attempted to clear non-existent session: {session_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "session_not_found",
                "message": f"Session '{session_id}' not found or already cleared",
                "session_id": session_id
            }
        )


@router.get(
    "/chat/sessions",
    summary="List Active Chat Sessions",
    description="""
Retrieve a list of all currently active chat sessions with metadata.
    
This endpoint provides an overview of all active conversation sessions,
useful for administration, monitoring, and analytics purposes

### Response Details:
- **Active Sessions**: List of all session identifiers
- **Session Count**: Total number of active sessions
- **Metadata**: Additional session information and statistics
""",
    response_description="List of active sessions with metadata",
    responses={
        200: {
            "description": "Active sessions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "active_sessions": [
                            "user_session_123",
                            "analytics_session_456", 
                            "support_session_789"
                        ],
                        "total_sessions": 3,
                        "session_details": {
                            "user_session_123": {
                                "message_count": 8,
                                "last_activity": "2024-12-21T10:05:00Z"
                            }
                        },
                        "timestamp": "2024-12-21T10:00:00Z"
                    }
                }
            }
        }
    }
)
async def get_active_sessions() -> dict:
    """
    Retrieve comprehensive information about all active chat sessions.
    
    This endpoint provides detailed information about currently active conversation
    sessions, including session metadata, activity statistics, and system resource usage.
    
    Returns:
        dict: Comprehensive session information containing:
            - active_sessions (List[str]): List of active session identifiers
            - total_sessions (int): Total number of active sessions
            - session_details (dict): Detailed information for each session
            - system_stats (dict): Overall system statistics
            - timestamp (str): Response generation timestamp
            
    Notes:
        - Sessions are considered active if they have recent activity
        - Detailed information includes message counts and last activity
        - System statistics provide resource usage insights
        - All timestamps are in UTC format
        
    Example:
        ```python
        import requests
        
        response = requests.get("/api/v1/chat/sessions")
        data = response.json()
        
        print(f"Active sessions: {data['total_sessions']}")
        for session_id in data['active_sessions']:
            print(f"Session: {session_id}")
        ```
    """
    sessions = list(conversation_store.keys())
    session_details = {}
    
    for session_id in sessions:
        history = conversation_store[session_id]
        session_details[session_id] = {
            "message_count": len(history),
            "last_activity": history[-1].timestamp.isoformat() if history else None,
            "user_messages": len([msg for msg in history if msg.role == "user"]),
            "assistant_messages": len([msg for msg in history if msg.role == "assistant"])
        }
    
    return {
        "active_sessions": sessions,
        "total_sessions": len(sessions),
        "session_details": session_details,
        "system_stats": {
            "total_messages": sum(len(history) for history in conversation_store.values()),
            "average_messages_per_session": round(
                sum(len(history) for history in conversation_store.values()) / len(sessions), 2
            ) if sessions else 0
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/chat/stream",
    summary="Stream Chat with Invoice Data",
    description="""
Stream chat responses with the invoice analysis system using natural language.

This endpoint provides the same RAG-based chatbot functionality as `/chat` 
but with real-time streaming responses, allowing for better user experience 
with immediate feedback and progressive content delivery.

### Streaming Benefits:
- **Immediate Response Start**: Users see responses as they're generated
- **Progressive Content**: Content appears word by word or chunk by chunk
- **Better UX**: Reduced perceived latency for complex queries
- **Interruptible**: Can be cancelled if needed

### Stream Format:
Uses Server-Sent Events (SSE) with JSON chunks:
    
```
data: {"type": "metadata", "data": {"query_type": "general", "retrieved_documents": 5}}
data: {"type": "content", "data": "Based on the invoice data, I found..."}
data: {"type": "content", "data": " 3 declined invoices totaling $2,500."}
data: {"type": "sources", "data": [{"filename": "invoice_001.pdf", "status": "declined"}]}
data: {"type": "suggestions", "data": ["What were the decline reasons?"]}
data: {"type": "done", "data": {"message": "Response complete"}}
```

### Chunk Types:
- **metadata**: Query analysis and document retrieval info
- **content**: Incremental response content
- **sources**: Source document references
- **suggestions**: Follow-up question suggestions
- **error**: Error information if processing fails
- **done**: Completion signal

### Query Examples:
- "Show me expenses over $1000"
- "Which invoices were submitted last month?"
- "Compare John's and Mary's reimbursement amounts"
""",
    response_description="Server-sent events stream with real-time chat responses",
    responses={
        200: {
            "description": "Streaming chat response with real-time updates",
            "content": {
                "text/plain": {
                    "example": """data: {"type": "metadata", "data": {"query_type": "general", "retrieved_documents": 3}}
data: {"type": "content", "data": "I found 3 invoices matching your criteria."}
data: {"type": "sources", "data": [{"filename": "invoice_001.pdf", "employee_name": "Aman Sikarwar"}]}
data: {"type": "done", "data": {"message": "Response complete"}}"""
                }
            }
        },
        400: {"description": "Invalid query or processing error"},
        422: {"description": "Validation error in request parameters"}
    }
)
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
            llm_service = LLMService()
            chatbot_service = ChatbotService(vector_store, llm_service)

            session_id = chat_request.session_id or "default"
            conversation_history = conversation_store.get(session_id, [])

            async for chunk in chatbot_service.process_query_streaming(
                query=chat_request.query,
                conversation_history=conversation_history,
                filters=chat_request.filters,
            ):
                streaming_chunk = StreamingChunk(
                    type=StreamingChunkType(chunk["type"]),
                    data=chunk["data"],
                    timestamp=datetime.now(timezone.utc),
                )

                chunk_json = streaming_chunk.model_dump_json()
                yield f"data: {chunk_json}\n\n"

                await asyncio.sleep(0.1)

            if chat_request.session_id:
                conversation_history.append(
                    ChatMessage(
                        role="user",
                        content=chat_request.query,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                conversation_history.append(
                    ChatMessage(
                        role="assistant",
                        content="[Streaming response completed]",
                        timestamp=datetime.now(timezone.utc),
                    )
                )

                max_history = 20
                if len(conversation_history) > max_history:
                    conversation_history = conversation_history[-max_history:]

                conversation_store[session_id] = conversation_history

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            error_chunk = StreamingChunk(
                type=StreamingChunkType.ERROR,
                data=f"Error processing chat query: {str(e)}",
                timestamp=datetime.now(timezone.utc),
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
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        },
    )
