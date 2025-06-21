"""
Chatbot Service.

This service orchestrates the RAG (Retrieval Augmented Generation) chatbot
functionality by combining vector search with LLM responses.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    ChatMessage,
    DocumentSource,
    ReimbursementStatus,
    SearchFilters,
)
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Service for handling chatbot interactions using RAG.

    This service combines vector search capabilities with LLM response generation
    to provide intelligent querying of invoice reimbursement data.
    """

    def __init__(self, vector_store: VectorStoreService, llm_service: LLMService):
        """
        Initialize the chatbot service.

        Args:
            vector_store: Vector store service for document retrieval
            llm_service: LLM service for response generation
        """
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.logger = logger

    async def initialize(self):
        """
        Initialize the chatbot service.
        """
        try:
            policy_available = await self.vector_store.ensure_policy_context()

            if policy_available:
                self.logger.info("Chatbot service initialized with policy context")
            else:
                self.logger.warning(
                    "Chatbot service initialized but policy context may be incomplete"
                )

        except Exception as e:
            self.logger.error(f"Error initializing chatbot service: {e}")
            raise

    async def process_query(
        self,
        query: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        filters: Optional[SearchFilters] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query using RAG methodology.

        Args:
            query: User's natural language query
            conversation_history: Previous conversation messages
            filters: Optional search filters

        Returns:
            Dictionary containing response and metadata
        """
        self.logger.info(f"Processing query: {query[:100]}...")

        try:
            query_analysis = self._analyze_query(query, filters)

            retrieved_docs = await self._retrieve_documents(
                query, query_analysis["filters"], query_analysis["limit"]
            )

            policy_context = await self._retrieve_policy_context(query)

            all_context_docs = retrieved_docs + policy_context

            response = await self.llm_service.generate_chat_response(
                query=query,
                context_documents=all_context_docs,
                conversation_history=self._format_conversation_history(
                    conversation_history
                ),
            )

            suggestions = await self.llm_service.generate_query_suggestions(
                original_query=query,
                context_documents=all_context_docs,
                query_type=query_analysis["type"],
            )

            invoice_sources = self._prepare_sources(retrieved_docs)
            policy_sources = self._prepare_sources(policy_context)

            return {
                "response": response,
                "sources": invoice_sources,
                "policy_sources": policy_sources,
                "retrieved_documents": len(retrieved_docs),
                "policy_documents": len(policy_context),
                "query_type": query_analysis["type"],
                "filters_applied": query_analysis["filters"],
                "suggestions": suggestions,
            }

        except Exception as e:
            self.logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "response": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                "sources": [],
                "retrieved_documents": 0,
                "query_type": "error",
                "filters_applied": {},
                "suggestions": [
                    "Show me all invoices",
                    "List declined invoices",
                    "Show me approved invoices",
                    "What are the expense categories?",
                ],
            }

    async def process_query_streaming(
        self,
        query: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        filters: Optional[SearchFilters] = None,
    ):
        """
        Process a user query using RAG methodology with streaming response.

        Args:
            query: User's natural language query
            conversation_history: Previous conversation messages
            filters: Optional search filters

        Yields:
            Streaming response chunks and metadata with optimized performance
        """
        self.logger.info(f"Processing streaming query: {query[:100]}...")

        start_time = datetime.now()

        try:
            query_analysis = self._analyze_query(query, filters)

            retrieved_docs = await self._retrieve_documents(
                query, query_analysis["filters"], query_analysis["limit"]
            )

            policy_context = await self._retrieve_policy_context(query)

            all_context_docs = retrieved_docs + policy_context

            metadata = {
                "sources": self._prepare_sources(retrieved_docs),
                "policy_sources": self._prepare_sources(policy_context),
                "retrieved_documents": len(retrieved_docs),
                "policy_documents": len(policy_context),
                "query_type": query_analysis["type"],
                "filters_applied": query_analysis["filters"],
                "processing_time_ms": int(
                    (datetime.now() - start_time).total_seconds() * 1000
                ),
            }

            yield {"type": "metadata", "data": metadata}

            chunk_count = 0
            response_start_time = datetime.now()

            async for chunk in self.llm_service.generate_chat_response_streaming(
                query=query,
                context_documents=all_context_docs,
                conversation_history=self._format_conversation_history(
                    conversation_history
                ),
            ):
                chunk_count += 1
                yield {"type": "content", "data": chunk}

            response_time = int(
                (datetime.now() - response_start_time).total_seconds() * 1000
            )
            self.logger.info(
                f"Streaming response completed: {chunk_count} chunks in {response_time}ms"
            )

            try:
                # Use asyncio.wait_for to prevent hanging on suggestions
                suggestions = await asyncio.wait_for(
                    self.llm_service.generate_query_suggestions(
                        original_query=query,
                        context_documents=all_context_docs,
                        query_type=query_analysis["type"],
                    ),
                    timeout=10.0,
                )

                yield {"type": "suggestions", "data": suggestions}
            except asyncio.TimeoutError:
                self.logger.warning("Suggestions generation timed out, using fallbacks")
                yield {
                    "type": "suggestions",
                    "data": [
                        "Show me all invoices",
                        "List declined invoices",
                        "Show me approved invoices",
                        "What are the expense categories?",
                    ],
                }
            except Exception as e:
                self.logger.error(f"Error generating suggestions: {e}")
                yield {
                    "type": "suggestions",
                    "data": [
                        "Show me all invoices",
                        "List declined invoices",
                        "Show me approved invoices",
                        "What are the expense categories?",
                    ],
                }

            total_time = int((datetime.now() - start_time).total_seconds() * 1000)
            yield {
                "type": "done",
                "data": {
                    "total_processing_time_ms": total_time,
                    "chunks_streamed": chunk_count,
                    "documents_retrieved": len(retrieved_docs),
                },
            }

        except Exception as e:
            self.logger.error(f"Error processing streaming query: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": f"I apologize, but I encountered an error while processing your request: {str(e)}",
            }

    def _analyze_query(
        self, query: str, filters: Optional[SearchFilters] = None
    ) -> Dict[str, Any]:
        """
        Analyze the user query to determine search strategy.

        Args:
            query: User query
            filters: Optional search filters

        Returns:
            Dictionary containing query analysis results
        """
        query_lower = query.lower()

        analysis = {"type": "general", "filters": {}, "limit": 10}

        if filters:
            if filters.employee_name:
                analysis["filters"]["employee_name"] = filters.employee_name
                analysis["type"] = "employee_specific"

            if filters.status:
                analysis["filters"]["status"] = filters.status.value
                analysis["type"] = "status_filter"

        if "for " in query_lower or "by " in query_lower:
            words = query_lower.split()
            for i, word in enumerate(words):
                if word in ["for", "by"] and i + 1 < len(words):
                    potential_name = " ".join(words[i + 1 : i + 3]).title()
                    potential_name = potential_name.strip(".,!?:;")
                    if len(potential_name) > 2:
                        analysis["filters"]["employee_name"] = potential_name
                        analysis["type"] = "employee_specific"
                    break

        status_keywords = {
            "declined": "declined",
            "rejected": "declined",
            "denied": "declined",
            "approved": "fully_reimbursed",
            "reimbursed": "fully_reimbursed",
            "partial": "partially_reimbursed",
            "partially": "partially_reimbursed",
        }

        for keyword, status in status_keywords.items():
            if keyword in query_lower:
                analysis["filters"]["status"] = status
                if analysis["type"] == "general":
                    analysis["type"] = "status_filter"
                break

        if "all" in query_lower or "list" in query_lower:
            analysis["limit"] = 50
        elif "few" in query_lower or "some" in query_lower:
            analysis["limit"] = 5

        return analysis

    async def _retrieve_documents(
        self, query: str, filters: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from the vector store.

        Args:
            query: Search query
            filters: Search filters
            limit: Maximum number of documents

        Returns:
            List of retrieved documents
        """
        try:
            score_threshold = 0.1 if filters else 0.3

            search_results = await self.vector_store.search_similar_invoices(
                query_text=query,
                filters=filters,
                limit=limit,
                score_threshold=score_threshold,
            )

            documents = []
            for result in search_results:
                doc_dict = {
                    "id": result.document.id,
                    "content": result.document.content,
                    "metadata": result.document.metadata,
                    "score": result.score,
                }
                documents.append(doc_dict)

            self.logger.info(f"Retrieved {len(documents)} documents for query")
            return documents

        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []

    def _format_conversation_history(
        self, conversation_history: Optional[List[ChatMessage]] = None
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for LLM consumption with enhanced context awareness.

        Args:
            conversation_history: List of chat messages

        Returns:
            Formatted conversation history
        """
        if not conversation_history:
            return []

        formatted = []

        recent_messages = conversation_history[-6:]

        for msg in recent_messages:
            formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    def _prepare_sources(self, documents: List[Dict[str, Any]]) -> List[DocumentSource]:
        """
        Prepare source information from retrieved documents.

        Args:
            documents: Retrieved documents

        Returns:
            List of DocumentSource objects
        """
        sources = []

        for doc in documents[:10]:
            metadata = doc.get("metadata", {})

            content = doc.get("content", "")
            excerpt = content[:200] + "..." if len(content) > 200 else content

            raw_status = metadata.get("status", "declined")
            if raw_status == "unknown":
                raw_status = "declined"

            try:
                status = ReimbursementStatus(raw_status)
            except ValueError:
                status = ReimbursementStatus.DECLINED

            source = DocumentSource(
                document_id=doc.get("id", ""),
                filename=metadata.get("invoice_filename", "Unknown"),
                employee_name=metadata.get("employee_name", "Unknown"),
                status=status,
                similarity_score=doc.get("score", 0.0),
                excerpt=excerpt,
            )
            sources.append(source)

        return sources

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the invoice database.

        Returns:
            Dictionary containing statistics
        """
        try:
            collection_stats = await self.vector_store.get_collection_stats()

            return {
                "total_invoices": collection_stats.get("total_documents", 0),
                "collection_status": collection_stats.get("status", "unknown"),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}

    async def search_by_employee(
        self, employee_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for invoices by employee name.

        Args:
            employee_name: Name of the employee
            limit: Maximum number of results

        Returns:
            List of invoice documents
        """
        try:
            filters = {"employee_name": employee_name}

            search_results = await self.vector_store.search_similar_invoices(
                query_text=f"invoices for {employee_name}",
                filters=filters,
                limit=limit,
                score_threshold=0.1,
            )

            return [
                {
                    "id": result.document.id,
                    "content": result.document.content,
                    "metadata": result.document.metadata,
                    "score": result.score,
                }
                for result in search_results
            ]

        except Exception as e:
            self.logger.error(f"Error searching by employee {employee_name}: {e}")
            return []

    async def search_by_status(
        self, status: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for invoices by reimbursement status.

        Args:
            status: Reimbursement status
            limit: Maximum number of results

        Returns:
            List of invoice documents
        """
        try:
            filters = {"status": status}

            search_results = await self.vector_store.search_similar_invoices(
                query_text=f"{status} invoices",
                filters=filters,
                limit=limit,
                score_threshold=0.1,
            )

            return [
                {
                    "id": result.document.id,
                    "content": result.document.content,
                    "metadata": result.document.metadata,
                    "score": result.score,
                }
                for result in search_results
            ]

        except Exception as e:
            self.logger.error(f"Error searching by status {status}: {e}")
            return []

    def _query_needs_policy_context(self, query: str) -> bool:
        """
        Determine if a query might benefit from policy context.

        Args:
            query: User query

        Returns:
            True if the query likely needs policy information
        """
        query_lower = query.lower()

        policy_keywords = [
            "policy",
            "rule",
            "limit",
            "maximum",
            "minimum",
            "allowed",
            "eligible",
            "reimbursable",
            "not reimbursed",
            "violation",
            "guidelines",
            "requirements",
            "approval",
            "criteria",
            "what expenses",
            "which expenses",
            "how much",
            "spending limit",
            "per diem",
            "allowance",
            "procedure",
            "process",
            "documentation",
        ]

        return any(keyword in query_lower for keyword in policy_keywords)

    async def _retrieve_policy_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant policy context for the query.
        Always tries to get policy context to provide comprehensive responses.

        Args:
            query: User query

        Returns:
            List of policy document excerpts
        """
        try:
            policy_results = await self.vector_store.search_policy_context(
                query_text=query,
                limit=2,
                score_threshold=0.1,
            )

            policy_docs = []
            for result in policy_results:
                doc_dict = {
                    "id": result.document.id,
                    "content": result.document.content,
                    "metadata": result.document.metadata,
                    "score": result.score,
                    "type": "policy",
                }
                policy_docs.append(doc_dict)

            self.logger.info(
                f"Retrieved {len(policy_docs)} policy documents for context"
            )
            return policy_docs

        except Exception as e:
            self.logger.error(f"Error retrieving policy context: {e}")
            return []

    async def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available context in the vector database.

        Returns:
            Dictionary containing context statistics and information
        """
        try:
            stats = await self.vector_store.get_collection_stats()

            invoice_results = await self.vector_store.search_similar_invoices(
                query_text="invoice analysis",
                limit=1000,
                score_threshold=0.0,
            )

            policy_results = await self.vector_store.search_policy_context(
                query_text="policy",
                limit=1000,
                score_threshold=0.0,
            )

            employees = set()
            statuses = {"fully_reimbursed": 0, "partially_reimbursed": 0, "declined": 0}
            total_amount = 0.0

            for result in invoice_results:
                metadata = result.document.metadata
                if metadata.get("employee_name"):
                    employees.add(metadata.get("employee_name"))

                status = metadata.get("status", "")
                if status in statuses:
                    statuses[status] += 1

                amount = metadata.get("total_amount", 0)
                if isinstance(amount, (int, float)):
                    total_amount += amount

            return {
                "collection_stats": stats,
                "invoice_documents": len(invoice_results),
                "policy_documents": len(policy_results),
                "unique_employees": len(employees),
                "employee_names": sorted(list(employees)),
                "status_breakdown": statuses,
                "total_invoice_amount": total_amount,
                "context_coverage": {
                    "has_invoices": len(invoice_results) > 0,
                    "has_policies": len(policy_results) > 0,
                    "full_context": len(invoice_results) > 0
                    and len(policy_results) > 0,
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting context summary: {e}")
            return {
                "error": str(e),
                "context_coverage": {
                    "has_invoices": False,
                    "has_policies": False,
                    "full_context": False,
                },
            }
