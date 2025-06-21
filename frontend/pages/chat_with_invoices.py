"""
Chat with Invoices Page for Streamlit Frontend

This page provides a conversational interface for querying processed invoice data
with real-time streaming responses from the backend.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st


def format_currency(amount: float, currency: str = "INR") -> str:
    """Format currency with proper symbol."""
    symbols = {"INR": "₹", "USD": "$", "EUR": "€"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def get_status_color(status: str) -> str:
    """Get color for reimbursement status."""
    colors = {
        "fully_reimbursed": "success",
        "partially_reimbursed": "warning",
        "declined": "error",
    }
    return colors.get(status.lower(), "info")


def get_status_icon(status: str) -> str:
    """Get icon for reimbursement status."""
    icons = {"fully_reimbursed": "✅", "partially_reimbursed": "⚠️", "declined": "❌"}
    return icons.get(status.lower(), "ℹ️")


def stream_chat_response(
    query: str, session_id: str, filters: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Stream chat response with real-time updates.

    Args:
        query: User query
        session_id: Session identifier
        filters: Optional search filters

    Returns:
        Dictionary containing response and metadata
    """
    api_url = "http://localhost:8000/api/v1/chat/stream"

    request_data = {
        "query": query,
        "session_id": session_id,
        "include_sources": True,
    }

    if filters:
        request_data["filters"] = filters

    response_data = {
        "content": "",
        "metadata": {},
        "sources": [],
        "suggestions": [],
        "errors": [],
        "chunks_received": 0,
    }

    content_placeholder = st.empty()

    try:
        with httpx.stream(
            "POST", api_url, json=request_data, timeout=300.0
        ) as response:
            if response.status_code != 200:
                error_text = response.text
                st.error(f"❌ HTTP {response.status_code}: {error_text}")
                return response_data

            accumulated_content = ""

            for line in response.iter_lines():
                if line.startswith("data:"):
                    try:
                        chunk_data = line[5:]  # Remove 'data: ' prefix
                        if not chunk_data.strip():
                            continue

                        chunk = json.loads(chunk_data)
                        response_data["chunks_received"] += 1

                        chunk_type = chunk.get("type")
                        chunk_payload = chunk.get("data", {})

                        if chunk_type == "metadata":
                            response_data["metadata"] = chunk_payload
                            docs_count = chunk_payload.get("retrieved_documents", 0)
                            query_type = chunk_payload.get("query_type", "unknown")

                            if docs_count > 0:
                                with st.status(
                                    f"Found {docs_count} relevant documents ({query_type})",
                                    state="running",
                                ):
                                    time.sleep(0.5)

                        elif chunk_type == "content":
                            accumulated_content += chunk_payload
                            response_data["content"] = accumulated_content

                            content_placeholder.markdown(accumulated_content + "▌")

                        elif chunk_type == "suggestions":
                            response_data["suggestions"] = chunk_payload

                        elif chunk_type == "sources":
                            response_data["sources"] = chunk_payload

                        elif chunk_type == "done":
                            content_placeholder.markdown(accumulated_content)
                            break

                        elif chunk_type == "error":
                            error_msg = chunk_payload
                            response_data["errors"].append(error_msg)
                            st.error(f"❌ {error_msg}")
                            break

                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        st.error(f"❌ Streaming error: {str(e)}")
        response_data["errors"].append(f"Streaming error: {str(e)}")

    return response_data


def display_sources(sources: List[Dict[str, Any]]):
    """Display source documents used in the response."""
    if not sources:
        return

    with st.expander(f"📚 Sources ({len(sources)} documents)", expanded=False):
        for i, source in enumerate(sources, 1):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{i}. {source.get('filename', 'Unknown')}**")
                st.write(f"Employee: {source.get('employee_name', 'Unknown')}")
                if source.get("excerpt"):
                    st.write(f"Excerpt: _{source.get('excerpt', '')}_")

            with col2:
                status = source.get("status", "unknown")
                st.write(
                    f"{get_status_icon(status)} {status.replace('_', ' ').title()}"
                )
                similarity = source.get("similarity_score", 0)
                st.write(f"Similarity: {similarity:.2%}")


def display_suggestions(suggestions: List[str], session_id: str):
    """Display suggested follow-up questions as clickable buttons."""
    if not suggestions:
        return

    st.subheader("💡 Suggested Questions")

    cols = st.columns(min(len(suggestions), 2))

    for i, suggestion in enumerate(suggestions):
        with cols[i % len(cols)]:
            if st.button(
                suggestion, key=f"suggestion_{session_id}_{i}", use_container_width=True
            ):
                st.session_state.chat_history.append(
                    {"role": "user", "content": suggestion, "timestamp": time.time()}
                )

                process_chat_message(suggestion, session_id)
                st.rerun()


def process_chat_message(query: str, session_id: str, filters: Optional[Dict] = None):
    """Process a chat message and add the response to chat history."""

    with st.chat_message("assistant"):
        response_data = stream_chat_response(query, session_id, filters)

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": response_data["content"],
            "metadata": response_data["metadata"],
            "sources": response_data["sources"],
            "suggestions": response_data["suggestions"],
            "timestamp": time.time(),
        }
    )

    if response_data["sources"]:
        display_sources(response_data["sources"])

    if response_data["suggestions"]:
        display_suggestions(response_data["suggestions"], session_id)


def main():
    """Main function for the Chat with Invoices page."""

    st.title("💬 Chat with Processed Invoices")
    st.subheader(
        "Ask questions about your processed invoices using natural language AI"
    )

    # if st.session_state.analysis_results:
    #     results = st.session_state.analysis_results
    #     col1, col2, col3 = st.columns(3)
    #     with col1:
    #         st.metric("✅ Processed", results.get("processed_invoices", 0))
    #     with col2:
    #         st.metric("❌ Failed", results.get("failed_invoices", 0))
    #     with col3:
    #         employee = results.get("employee_name", "Unknown")
    #         st.metric("👤 Employee", employee[:15] if len(employee) > 15 else employee)

    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        with st.container():
            st.info(
                f"💼 **Current Analysis:** {results.get('employee_name', 'Unknown Employee')} • "
                f"{results.get('processed_invoices', 0)} invoices processed • "
                f"{results.get('failed_invoices', 0)} failed"
            )

    if not st.session_state.analysis_results:
        st.warning("⚠️ No invoice analysis results found.")

        st.markdown("### 🔍 To use the chat feature:")
        col1, col2 = st.columns(2)
        with col1:
            st.info(
                "**1. Process Invoices First**\nYou need to analyze some invoices before you can chat about them."
            )
        with col2:
            st.info(
                "**2. Ask Questions**\nOnce invoices are processed, you can ask questions about the results."
            )

        from utils.streamlit_utils import check_backend_health

        health_status = check_backend_health()
        if health_status["status"] != "online":
            st.error(f"❌ Backend Status: {health_status['message']}")
            st.info(
                "💡 **Note**: Both the analysis and chat features require the FastAPI backend to be running."
            )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "📄 Go to Invoice Analysis", type="primary", use_container_width=True
            ):
                st.session_state.selected_page = "📄 Invoice Analysis"
                st.rerun()
        return

    main_chat_col, sidebar_col = st.columns([3, 1])

    # MAIN CHAT AREA (Left Column)
    with main_chat_col:
        # if len(st.session_state.chat_history) > 2:
        #     recent_queries = [
        #         msg
        #         for msg in st.session_state.chat_history[-6:]
        #         if msg["role"] == "user"
        #     ]
        #     if len(recent_queries) > 1:
        #         with st.expander("🧠 Recent Context", expanded=False):
        #             st.write("Recent queries in this conversation:")
        #             for i, query in enumerate(recent_queries[-3:], 1):
        #                 st.write(f"{i}. {query['content']}")

        chat_container = st.container()
        with chat_container:
            if len(st.session_state.chat_history) == 0:
                st.markdown("""
                ### Welcome to AI-Powered Invoice Chat!
                
                I'm your intelligent assistant here to help you explore and analyze your processed invoices. 
                You can ask me questions like:
                """)

                col1, col2 = st.columns(2)

                with col1:
                    st.info("Show me all declined invoices")
                    st.info("Which employees have pending reimbursements?")

                with col2:
                    st.info("What are the most expensive invoices?")
                    st.info("Summarize the analysis results")

                st.success(
                    "💡 **Pro Tip:** Use the filters in the sidebar to narrow down results, then ask questions about specific data!"
                )

            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    if message["role"] == "assistant" and message.get("sources"):
                        display_sources(message["sources"])

                    if message["role"] == "assistant" and message.get("metadata"):
                        metadata = message["metadata"]
                        if metadata.get("retrieved_documents", 0) > 0:
                            with st.expander("🔍 Query Analysis", expanded=False):
                                st.write(
                                    f"**Query Type:** {metadata.get('query_type', 'Unknown')}"
                                )
                                st.write(
                                    f"**Documents Used:** {metadata.get('retrieved_documents', 0)}"
                                )
                                if metadata.get("filters_applied"):
                                    st.write(
                                        f"**Filters Applied:** {metadata['filters_applied']}"
                                    )

        if prompt := st.chat_input("Ask a question about your invoices..."):
            filters = {}
            if "current_filters" in st.session_state:
                filters = st.session_state.current_filters

            st.session_state.chat_history.append(
                {"role": "user", "content": prompt, "timestamp": time.time()}
            )

            with st.chat_message("user"):
                st.markdown(prompt)

            process_chat_message(
                prompt, st.session_state.chat_session_id, filters if filters else None
            )
            st.rerun()

    # SIDEBAR CONTROLS (Right Column)
    with sidebar_col:
        st.subheader("🔍 Search Filters")

        default_employee = ""
        if "auto_employee_filter" in st.session_state:
            default_employee = st.session_state.auto_employee_filter
            del st.session_state.auto_employee_filter

        employee_filter = st.text_input(
            "Employee Name",
            value=default_employee,
            placeholder="Filter by employee name",
            help="Filter results by specific employee",
        )

        # Status filter
        status_filter = st.selectbox(
            "Reimbursement Status",
            options=["", "fully_reimbursed", "partially_reimbursed", "declined"],
            format_func=lambda x: x.replace("_", " ").title() if x else "All Statuses",
            help="Filter by reimbursement status",
        )

        with st.expander("Amount Filters", expanded=False):
            min_amount = st.number_input(
                "Minimum Amount", min_value=0.0, value=0.0, step=100.0
            )
            max_amount = st.number_input(
                "Maximum Amount", min_value=0.0, value=0.0, step=100.0
            )

        filters = {}
        if employee_filter:
            filters["employee_name"] = employee_filter
        if status_filter:
            filters["status"] = status_filter
        if min_amount > 0:
            filters["min_amount"] = min_amount
        if max_amount > 0:
            filters["max_amount"] = max_amount

        st.session_state.current_filters = filters

        if filters:
            st.subheader("Active Filters")
            for key, value in filters.items():
                st.text(f"{key.replace('_', ' ').title()}: {value}")

        # Clear filters button
        if st.button(
            "Clear Filters", use_container_width=True, key="clear_filters_btn"
        ):
            st.session_state.current_filters = {}
            st.rerun()

        st.markdown("---")

        # Chat statistics
        st.subheader("Chat Stats")
        total_messages = len(st.session_state.chat_history)
        assistant_messages = len(
            [m for m in st.session_state.chat_history if m["role"] == "assistant"]
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total", total_messages)
        with col_b:
            st.metric("Q&A Pairs", assistant_messages)

        if st.button(
            "🗑️ Clear Chat",
            type="secondary",
            use_container_width=True,
            key="clear_chat_btn",
        ):
            st.session_state.chat_history = []
            st.session_state.chat_session_id = str(uuid.uuid4())
            st.rerun()

        st.markdown("---")

        st.subheader("🔗 Quick Actions")
        if st.button(
            "📄 Back to Analysis", use_container_width=True, key="back_to_analysis_btn"
        ):
            st.session_state.selected_page = "📄 Invoice Analysis"
            st.rerun()

        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            employee = results.get("employee_name", "Unknown")
            if st.button(
                f"👤 {employee[:15]}{'...' if len(employee) > 15 else ''}",
                use_container_width=True,
                help=f"Current analysis for: {employee}",
                key="employee_filter_btn",
            ):
                st.session_state.auto_employee_filter = employee
                st.rerun()

    if len(st.session_state.chat_history) == 0:
        st.markdown("---")
        st.subheader("💡 Get Started - Try These Questions")
        st.markdown("Click on any example to begin chatting:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Analysis & Stats**")
            basic_queries = [
                "Show me all declined invoices",
                "What are the most expensive invoices?",
                "Summarize the reimbursement statistics",
            ]
            for i, query in enumerate(basic_queries):
                if st.button(query, key=f"basic_{i}", use_container_width=True):
                    # Add to chat and process
                    st.session_state.chat_history.append(
                        {"role": "user", "content": query, "timestamp": time.time()}
                    )
                    process_chat_message(
                        query,
                        st.session_state.chat_session_id,
                        filters if filters else None,
                    )
                    st.rerun()

        with col2:
            st.markdown("**Specific Queries**")
            specific_queries = [
                "Which employees have the highest amounts?",
                "What are the common policy violations?",
                "Show me all invoices over ₹5000",
            ]
            for i, query in enumerate(specific_queries):
                if st.button(query, key=f"specific_{i}", use_container_width=True):
                    st.session_state.chat_history.append(
                        {"role": "user", "content": query, "timestamp": time.time()}
                    )
                    process_chat_message(
                        query,
                        st.session_state.chat_session_id,
                        filters if filters else None,
                    )
                    st.rerun()
    else:
        with st.expander("💡 More Query Ideas", expanded=False):
            st.markdown("**Try asking about:**")
            suggestions = [
                "• Policy violations in detail",
                "• Comparison between employees",
                "• Trends in reimbursement amounts",
                "• Specific invoice details",
                "• Date-based analysis",
            ]
            for suggestion in suggestions:
                st.write(suggestion)


if __name__ == "__main__":
    main()
