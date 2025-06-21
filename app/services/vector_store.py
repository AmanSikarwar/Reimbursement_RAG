"""
Vector Store Service.

This service handles interactions with the Qdrant vector database for storing
and retrieving invoice analysis embeddings.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.schemas import SearchResult, VectorDocument

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for managing vector storage and retrieval using Qdrant.

    This class handles embedding generation, document storage, and similarity search
    for invoice analysis data.
    """

    def __init__(self):
        """Initialize the vector store service."""
        self.logger = logger
        self.client: Optional[QdrantClient] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.collection_name = settings.COLLECTION_NAME
        self.vector_size = settings.VECTOR_SIZE

    async def initialize(self):
        """
        Initialize the Qdrant client and embedding model.

        Sets up the connection to Qdrant and loads the embedding model.
        Also creates the collection if it doesn't exist.
        """
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
            )

            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

            await self._create_collection_if_not_exists()

            self.logger.info("Vector store service initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing vector store: {e}", exc_info=True)
            raise

    async def _create_collection_if_not_exists(self):
        """Create the collection if it doesn't already exist."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        try:
            self.client.get_collection(self.collection_name)
            self.logger.info(f"Collection already exists: {self.collection_name}")
            await self._create_payload_indexes()
            return
        except Exception:
            pass

        if self.vector_size is None:
            raise ValueError(
                "Vector size not initialized. Ensure embedding model is loaded first."
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size, distance=Distance.COSINE
            ),
        )
        self.logger.info(f"Created collection: {self.collection_name}")
        await self._create_payload_indexes()

    async def _create_payload_indexes(self):
        """Create payload indexes for efficient filtering."""
        if not self.client:
            raise ValueError("Qdrant client not initialized")

        try:
            from qdrant_client.http.models import PayloadSchemaType

            indexes_to_create = [
                ("status", PayloadSchemaType.KEYWORD),
                ("employee_name", PayloadSchemaType.KEYWORD),
                ("doc_type", PayloadSchemaType.KEYWORD),
                ("currency", PayloadSchemaType.KEYWORD),
                ("file_hash", PayloadSchemaType.KEYWORD),  # Add file hash index
                ("total_amount", PayloadSchemaType.FLOAT),
                ("reimbursement_amount", PayloadSchemaType.FLOAT),
            ]

            for field_name, field_schema in indexes_to_create:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=field_schema,
                    )
                    self.logger.info(f"Created index for field: {field_name}")
                except Exception as e:
                    if (
                        "already exists" in str(e).lower()
                        or "already indexed" in str(e).lower()
                    ):
                        self.logger.debug(
                            f"Index already exists for field: {field_name}"
                        )
                    else:
                        self.logger.warning(
                            f"Failed to create index for {field_name}: {e}"
                        )

            self.logger.info("Payload indexes creation completed")

        except Exception as e:
            self.logger.error(f"Error creating payload indexes: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding
        """
        if not self.embedding_model:
            raise ValueError("Embedding model not initialized")

        try:
            embedding = self.embedding_model.encode(text)
            # Convert numpy array or tensor to list of floats
            if hasattr(embedding, "tolist"):
                return embedding.tolist()
            elif isinstance(embedding, (list, tuple)):
                return [float(x) for x in embedding]
            else:
                return [float(x) for x in embedding]
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise

    async def check_file_exists(
        self, file_hash: str, doc_type: str = "invoice_analysis"
    ) -> Optional[VectorDocument]:
        """
        Check if a file with the given hash already exists in the vector store.

        Args:
            file_hash: SHA-256 hash of the file content
            doc_type: Type of document to search for (default: "invoice_analysis")

        Returns:
            VectorDocument if file exists, None otherwise
        """
        try:
            if not self.client:
                raise ValueError("Qdrant client not initialized")

            filter_conditions = Filter(
                must=[
                    FieldCondition(key="file_hash", match=MatchValue(value=file_hash)),
                    FieldCondition(key="doc_type", match=MatchValue(value=doc_type)),
                ]
            )

            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )

            if search_results[0]:
                point = search_results[0][0]
                payload = point.payload or {}

                return VectorDocument(
                    id=str(point.id),
                    content=payload.get("content", ""),
                    embedding=[],
                    metadata=payload,
                )

            return None

        except Exception as e:
            self.logger.error(
                f"Error checking file existence for hash {file_hash}: {e}"
            )
            return None

    async def check_invoice_exists(
        self, invoice_hash: str, employee_name: str
    ) -> Optional[VectorDocument]:
        """
        Check if an invoice with the given hash already exists for the employee.

        Args:
            invoice_hash: SHA-256 hash of the invoice file content
            employee_name: Name of the employee

        Returns:
            VectorDocument if invoice exists, None otherwise
        """
        try:
            if not self.client:
                raise ValueError("Qdrant client not initialized")

            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="file_hash", match=MatchValue(value=invoice_hash)
                    ),
                    FieldCondition(
                        key="doc_type", match=MatchValue(value="invoice_analysis")
                    ),
                    FieldCondition(
                        key="employee_name", match=MatchValue(value=employee_name)
                    ),
                ]
            )

            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )

            if search_results[0]:
                point = search_results[0][0]
                payload = point.payload or {}

                return VectorDocument(
                    id=str(point.id),
                    content=payload.get("content", ""),
                    embedding=[],
                    metadata=payload,
                )

            return None

        except Exception as e:
            self.logger.error(
                f"Error checking invoice existence for hash {invoice_hash}: {e}"
            )
            return None

    async def store_invoice_analysis(
        self,
        invoice_text: str,
        analysis_result: Dict[str, Any],
        employee_name: str,
        invoice_filename: str,
        file_hash: Optional[str] = None,
    ) -> str:
        """
        Store invoice analysis in the vector database.

        Args:
            invoice_text: Original invoice text
            analysis_result: LLM analysis result
            employee_name: Name of the employee
            invoice_filename: Original filename of the invoice
            file_hash: Optional SHA-256 hash of the file content

        Returns:
            Document ID of the stored record
        """
        try:
            doc_id = str(uuid.uuid4())

            content_for_embedding = f"""
            Invoice: {invoice_text}
            
            Analysis:
            Status: {analysis_result.get("status", "")}
            Reason: {analysis_result.get("reason", "")}
            Categories: {", ".join(analysis_result.get("categories", []))}
            """

            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_embedding, content_for_embedding
            )

            status_value = analysis_result.get("status", "")
            if hasattr(status_value, "value"):
                status_value = status_value.value
            elif str(status_value).startswith("ReimbursementStatus."):
                status_value = str(status_value).split(".")[-1].lower()

            metadata = {
                "employee_name": employee_name,
                "invoice_filename": invoice_filename,
                "status": status_value,
                "reason": analysis_result.get("reason", ""),
                "total_amount": analysis_result.get("total_amount", 0.0),
                "reimbursement_amount": analysis_result.get(
                    "reimbursement_amount", 0.0
                ),
                "currency": analysis_result.get("currency", "USD"),
                "categories": analysis_result.get("categories", []),
                "policy_violations": analysis_result.get("policy_violations", []),
                "date": datetime.now(timezone.utc).isoformat(),
                "doc_type": "invoice_analysis",
                "file_hash": file_hash,
            }

            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "content": invoice_text,
                    "analysis": analysis_result,
                    **metadata,
                },
            )

            if not self.client:
                raise ValueError("Qdrant client not initialized")
            self.client.upsert(collection_name=self.collection_name, points=[point])

            self.logger.info(f"Stored invoice analysis for {employee_name}: {doc_id}")
            return doc_id

        except Exception as e:
            self.logger.error(f"Error storing invoice analysis: {e}", exc_info=True)
            raise

    async def search_similar_invoices(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        score_threshold: float = 0.5,
    ) -> List[SearchResult]:
        """
        Search for similar invoices using vector similarity.

        Args:
            query_text: Text query to search for
            filters: Optional metadata filters
            limit: Maximum number of results
            score_threshold: Minimum similarity score threshold

        Returns:
            List of search results with documents and scores
        """
        try:
            query_embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_embedding, query_text
            )

            filter_conditions = None
            if filters:
                filter_conditions = self._build_filter_conditions(filters)

            if not self.client:
                raise ValueError("Qdrant client not initialized")

            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            results = []
            for result in search_results.points:
                payload = result.payload or {}
                doc = VectorDocument(
                    id=str(result.id),
                    content=payload.get("content", ""),
                    embedding=query_embedding,
                    metadata=payload,
                )

                search_result = SearchResult(document=doc, score=result.score)
                results.append(search_result)

            self.logger.info(f"Found {len(results)} similar invoices for query")
            return results

        except Exception as e:
            self.logger.error(f"Error searching similar invoices: {e}", exc_info=True)
            return []

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """
        Build Qdrant filter conditions from filter dictionary.

        Args:
            filters: Dictionary of filters

        Returns:
            Qdrant Filter object or None if no conditions
        """
        conditions = []

        if "employee_name" in filters and filters["employee_name"]:
            conditions.append(
                FieldCondition(
                    key="employee_name",
                    match=MatchValue(value=filters["employee_name"]),
                )
            )

        if "status" in filters and filters["status"]:
            conditions.append(
                FieldCondition(key="status", match=MatchValue(value=filters["status"]))
            )

        return Filter(must=conditions) if conditions else None

    async def get_document_by_id(self, doc_id: str) -> Optional[VectorDocument]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: Document identifier

        Returns:
            VectorDocument if found, None otherwise
        """
        try:
            if not self.client:
                raise ValueError("Qdrant client not initialized")

            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
                with_payload=True,
                with_vectors=True,
            )

            if result:
                point = result[0]
                payload = point.payload or {}
                vector = point.vector

                embedding: List[float] = []
                if vector:
                    if isinstance(vector, dict):
                        first_vector = list(vector.values())[0] if vector else []
                        embedding = self._flatten_to_float_list(first_vector)
                    elif isinstance(vector, list):
                        embedding = self._flatten_to_float_list(vector)
                    else:
                        embedding = []

                return VectorDocument(
                    id=str(point.id),
                    content=payload.get("content", ""),
                    embedding=embedding,
                    metadata=payload,
                )

            return None

        except Exception as e:
            self.logger.error(f"Error retrieving document {doc_id}: {e}")
            return None

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store.

        Args:
            doc_id: Document identifier

        Returns:
            True if deletion was successful
        """
        try:
            if not self.client:
                raise ValueError("Qdrant client not initialized")

            self.client.delete(
                collection_name=self.collection_name, points_selector=[doc_id]
            )

            self.logger.info(f"Deleted document: {doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary containing collection statistics
        """
        try:
            if not self.client:
                raise ValueError("Qdrant client not initialized")

            info = self.client.get_collection(self.collection_name)

            return {
                "collection_name": self.collection_name,
                "total_documents": info.points_count,
                "vector_size": self.vector_size,
                "distance_metric": "cosine",
                "status": "ready",
            }

        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the vector store.

        Returns:
            Dictionary with health status information

        Raises:
            Exception: If health check fails
        """
        if not self.client:
            raise Exception("Vector store client not initialized")

        try:
            collections = self.client.get_collections()

            collection_info = self.client.get_collection(self.collection_name)

            return {
                "status": "healthy",
                "collections_count": len(collections.collections) if collections else 0,
                "collection_name": self.collection_name,
                "collection_points": collection_info.points_count
                if collection_info
                else 0,
            }
        except Exception as e:
            self.logger.error(f"Vector store health check failed: {e}")
            raise Exception(f"Vector store unhealthy: {str(e)}")

    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get detailed collection information.

        Returns:
            Dictionary with collection details
        """
        if not self.client:
            raise Exception("Vector store client not initialized")

        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": collection_info.points_count if collection_info else 0,
                "status": collection_info.status if collection_info else "unknown",
                "vector_size": self.vector_size,
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection info: {e}")
            raise Exception(f"Collection access failed: {str(e)}")

    def _flatten_to_float_list(self, data: Any) -> List[float]:
        """
        Flatten nested vector data to a simple list of floats.

        Args:
            data: Vector data that could be nested or contain StrictFloat types

        Returns:
            List of float values
        """
        result = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    result.extend(self._flatten_to_float_list(item))
                else:
                    try:
                        result.append(float(item))
                    except (ValueError, TypeError):
                        continue
        else:
            try:
                result.append(float(data))
            except (ValueError, TypeError):
                pass
        return result

    async def store_policy_document(
        self,
        policy_text: str,
        policy_name: str = "HR_Reimbursement_Policy",
        organization: str = "Company",
        file_hash: Optional[str] = None,
    ) -> str:
        """
        Store HR policy document in the vector database for chatbot context.

        Args:
            policy_text: Full text of the HR policy document
            policy_name: Name/identifier for the policy
            organization: Organization name
            file_hash: Optional SHA-256 hash of the file content

        Returns:
            Document ID of the stored policy
        """
        try:
            doc_id = str(uuid.uuid4())

            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_embedding, policy_text
            )

            metadata = {
                "doc_type": "policy",
                "policy_name": policy_name,
                "organization": organization,
                "date": datetime.now(timezone.utc).isoformat(),
                "content_type": "hr_reimbursement_policy",
                "file_hash": file_hash,
            }

            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "content": policy_text,
                    **metadata,
                },
            )

            if not self.client:
                raise ValueError("Qdrant client not initialized")
            self.client.upsert(collection_name=self.collection_name, points=[point])

            self.logger.info(f"Stored policy document: {policy_name} with ID: {doc_id}")
            return doc_id

        except Exception as e:
            self.logger.error(f"Error storing policy document: {e}", exc_info=True)
            raise

    async def search_policy_context(
        self,
        query_text: str,
        limit: int = 3,
        score_threshold: float = 0.3,
    ) -> List[SearchResult]:
        """
        Search for relevant policy information based on query.

        Args:
            query_text: Search query
            limit: Maximum number of policy documents to retrieve
            score_threshold: Minimum similarity score

        Returns:
            List of relevant policy document excerpts
        """
        try:
            if not self.client or not self.embedding_model:
                raise ValueError("Vector store not properly initialized")

            query_embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_embedding, query_text
            )

            policy_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value="policy"),
                    )
                ]
            )

            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=policy_filter,
                limit=limit,
                score_threshold=score_threshold,
            )

            results = []
            for result in search_results:
                payload = result.payload or {}
                doc = VectorDocument(
                    id=str(result.id),
                    content=payload.get("content", ""),
                    embedding=[],
                    metadata=payload,
                )
                results.append(SearchResult(document=doc, score=result.score))

            self.logger.info(f"Retrieved {len(results)} policy documents for query")
            return results

        except Exception as e:
            self.logger.error(f"Error searching policy context: {e}")
            return []

    async def ensure_policy_context(self) -> bool:
        """
        Ensure policy context is available in the vector store.
        If no policy documents exist, store a default policy.

        Returns:
            True if policy context is available
        """
        try:
            policy_results = await self.search_policy_context("reimbursement", limit=1)

            if policy_results:
                self.logger.info("Policy documents already available in vector store")
                return True

            self.logger.error("No policy documents found")

            raise ValueError(
                "No policy documents found in vector store. Please upload a policy document."
            )

        except Exception as e:
            self.logger.error(f"Error ensuring policy context: {e}")
            return False

    async def check_policy_exists(self, policy_hash: str) -> Optional[VectorDocument]:
        """
        Check if a policy with the given hash already exists in the vector store.

        Args:
            policy_hash: SHA-256 hash of the policy file content

        Returns:
            VectorDocument if policy exists, None otherwise
        """
        return await self.check_file_exists(policy_hash, "policy")
