#!/usr/bin/env python3
"""
Advanced Streaming Client Example for Invoice Reimbursement System.

This script demonstrates how to consume the streaming chat endpoint
using Server-Sent Events (SSE) with proper error handling and
performance monitoring.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

import aiohttp


class StreamingChatClient:
    """
    Client for consuming streaming chat responses from the Invoice Reimbursement System.

    This client demonstrates best practices for handling Server-Sent Events (SSE)
    streaming responses with proper error handling, reconnection logic, and
    performance monitoring.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the streaming chat client.

        Args:
            base_url: Base URL of the FastAPI server
        """
        self.base_url = base_url
        self.stream_url = f"{base_url}/api/v1/chat/stream"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=300, connect=30
            )  # 5 min total, 30s connect
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def stream_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        include_sources: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Stream a query to the chat endpoint and collect the response.

        Args:
            query: User query to send
            session_id: Optional session ID for conversation history
            include_sources: Whether to include source documents
            filters: Optional search filters

        Returns:
            Dictionary containing the complete response and metadata
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request_data = {
            "query": query,
            "session_id": session_id or f"client_{int(time.time())}",
            "include_sources": include_sources,
        }

        if filters:
            request_data["filters"] = filters

        print(f"🚀 Streaming query: {query[:100]}...")
        print(f"📡 Endpoint: {self.stream_url}")

        start_time = time.time()
        response_data = {
            "content": "",
            "metadata": {},
            "suggestions": [],
            "performance": {},
            "chunks_received": 0,
            "errors": [],
        }

        try:
            async with self.session.post(
                self.stream_url,
                json=request_data,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

                print(f"✅ Connection established (HTTP {response.status})")
                print("📦 Receiving chunks...")

                first_chunk_time = None

                async for line in response.content:
                    line_text = line.decode("utf-8").strip()

                    if line_text.startswith("data: "):
                        chunk_data = line_text[6:]  # Remove 'data: ' prefix

                        if not chunk_data:
                            continue

                        try:
                            chunk = json.loads(chunk_data)
                            response_data["chunks_received"] += 1

                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                print(
                                    f"⚡ First chunk received in {first_chunk_time - start_time:.2f}s"
                                )

                            # Process different chunk types
                            chunk_type = chunk.get("type")
                            chunk_payload = chunk.get("data")

                            if chunk_type == "metadata":
                                response_data["metadata"] = chunk_payload
                                docs_count = chunk_payload.get("retrieved_documents", 0)
                                query_type = chunk_payload.get("query_type", "unknown")
                                print(
                                    f"📊 Metadata: {docs_count} docs retrieved, type: {query_type}"
                                )

                            elif chunk_type == "content":
                                response_data["content"] += chunk_payload
                                print(f"💬 {chunk_payload}", end="", flush=True)

                            elif chunk_type == "suggestions":
                                response_data["suggestions"] = chunk_payload
                                print(f"\n💡 Suggestions: {len(chunk_payload)} items")

                            elif chunk_type == "done":
                                completion_data = chunk_payload or {}
                                total_time = time.time() - start_time

                                print("\n✅ Streaming completed!")
                                print(f"⏱️  Total time: {total_time:.2f}s")
                                print(
                                    f"📈 Chunks received: {response_data['chunks_received']}"
                                )

                                # Add performance metrics
                                response_data["performance"] = {
                                    "total_time_seconds": total_time,
                                    "time_to_first_chunk": first_chunk_time - start_time
                                    if first_chunk_time
                                    else 0,
                                    "chunks_per_second": response_data[
                                        "chunks_received"
                                    ]
                                    / total_time
                                    if total_time > 0
                                    else 0,
                                    **completion_data,
                                }
                                break

                            elif chunk_type == "error":
                                error_msg = chunk_payload
                                response_data["errors"].append(error_msg)
                                print(f"\n❌ Error: {error_msg}")
                                break

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Invalid JSON in chunk: {e}")
                            response_data["errors"].append(f"JSON decode error: {e}")
                            continue

        except Exception as e:
            error_msg = f"Streaming error: {str(e)}"
            print(f"\n❌ {error_msg}")
            response_data["errors"].append(error_msg)

        return response_data

    def print_response_summary(self, response_data: Dict[str, Any]):
        """
        Print a formatted summary of the streaming response.

        Args:
            response_data: Response data from stream_query
        """
        print("\n" + "=" * 60)
        print("📊 STREAMING RESPONSE SUMMARY")
        print("=" * 60)

        # Content summary
        content = response_data.get("content", "")
        print(f"📝 Content length: {len(content)} characters")

        # Metadata summary
        metadata = response_data.get("metadata", {})
        if metadata:
            print(f"📊 Documents retrieved: {metadata.get('retrieved_documents', 0)}")
            print(f"🔍 Query type: {metadata.get('query_type', 'unknown')}")
            print(f"⚡ Processing time: {metadata.get('processing_time_ms', 0)}ms")

        # Suggestions summary
        suggestions = response_data.get("suggestions", [])
        print(f"💡 Suggestions: {len(suggestions)} items")

        # Performance summary
        performance = response_data.get("performance", {})
        if performance:
            print(f"⏱️  Total time: {performance.get('total_time_seconds', 0):.2f}s")
            print(
                f"🚀 Time to first chunk: {performance.get('time_to_first_chunk', 0):.2f}s"
            )
            print(
                f"📈 Chunks per second: {performance.get('chunks_per_second', 0):.1f}"
            )

        # Error summary
        errors = response_data.get("errors", [])
        if errors:
            print(f"❌ Errors: {len(errors)}")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
        else:
            print("✅ No errors encountered")


async def main():
    """
    Main function demonstrating streaming client usage.
    """
    print("🧪 Invoice Reimbursement System - Streaming Client Demo")
    print("=" * 60)

    # Test queries to demonstrate streaming
    test_queries = [
        "Show me all declined invoices",
        "What are the most expensive invoices this month?",
        "List all invoices for John Doe",
        "Show me invoices that violated company policy",
    ]

    async with StreamingChatClient() as client:
        for i, query in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}/{len(test_queries)}")
            print("-" * 40)

            try:
                response = await client.stream_query(
                    query=query, session_id=f"demo_session_{i}"
                )

                client.print_response_summary(response)

                # Wait between queries to avoid overwhelming the server
                if i < len(test_queries):
                    print("\n⏳ Waiting 2 seconds before next query...")
                    await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Test {i} failed: {e}")

    print("\n🎉 Streaming client demo completed!")


if __name__ == "__main__":
    # Note: This requires the FastAPI server to be running
    print("📌 Make sure the FastAPI server is running on http://localhost:8000")
    print("   Start it with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
