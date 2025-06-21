"""
Streamlit Frontend for Invoice Reimbursement System

This is the main entry point for the multi-page Streamlit application
that provides a user-friendly interface for the Invoice Reimbursement System.
"""

import uuid

import streamlit as st

st.set_page_config(
    page_title="Invoice Reimbursement System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from pages import chat_with_invoices, invoice_analysis
    from utils.streamlit_utils import check_backend_health
    from utils.theme import apply_theme
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error(
        "Please ensure you're running the Streamlit app from the correct directory."
    )
    st.info(
        "Try running: `streamlit run streamlit_app.py` from the project root directory"
    )
    st.stop()

apply_theme()

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "📄 Invoice Analysis"

pages = {
    "📄 Invoice Analysis": invoice_analysis,
    "💬 Chat with Invoices": chat_with_invoices,
}

with st.sidebar:
    st.markdown("### 🏢 Invoice Reimbursement")

    st.markdown("---")

    st.subheader("📋 Navigation")

    analysis_badge = ""
    if st.session_state.analysis_results:
        processed = st.session_state.analysis_results.get("processed_invoices", 0)
        analysis_badge = f" ({processed})"

    if st.button(
        f"📄 Invoice Analysis{analysis_badge}",
        use_container_width=True,
        type="primary"
        if st.session_state.selected_page == "📄 Invoice Analysis"
        else "secondary",
        key="nav_invoice_analysis",
    ):
        st.session_state.selected_page = "📄 Invoice Analysis"
        st.rerun()

    chat_badge = ""
    if len(st.session_state.chat_history) > 0:
        chat_badge = f" ({len(st.session_state.chat_history)})"

    if st.button(
        f"💬 Chat with Invoices{chat_badge}",
        use_container_width=True,
        type="primary"
        if st.session_state.selected_page == "💬 Chat with Invoices"
        else "secondary",
        key="nav_chat_invoices",
    ):
        st.session_state.selected_page = "💬 Chat with Invoices"
        st.rerun()

    selected_page = st.session_state.selected_page

    st.markdown("---")

    st.subheader("🔌 System Status")

    health_status = check_backend_health()

    if health_status["status"] == "online":
        st.success("✅ Backend Online")
        if health_status["data"]:
            with st.expander("📋 System Details", expanded=False):
                st.json(health_status["data"])
    elif health_status["status"] == "issues":
        st.warning("⚠️ Backend Issues")
        st.info(health_status["message"])
    else:
        st.error("❌ Backend Offline")
        st.info(health_status["message"])

        with st.expander("🚀 Quick Start Backend", expanded=False):
            st.code("# Start the FastAPI backend server")
            st.code("cd /path/to/project")
            st.code(
                "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
            )
            st.info(
                "The backend must be running on port 8000 for the frontend to work properly."
            )

    st.markdown("---")

    st.subheader("📊 Session Info")

    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            st.metric("📋 Invoices", f"{results.get('processed_invoices', 0)}")
            st.metric("💬 Messages", len(st.session_state.chat_history))
        else:
            st.metric("📋 Invoices", "0")
            st.metric("💬 Messages", len(st.session_state.chat_history))

    with col2:
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            st.metric("❌ Failed", f"{results.get('failed_invoices', 0)}")
            employee = results.get("employee_name", "Unknown")
            st.metric(
                "👤 Employee", employee[:10] + "..." if len(employee) > 10 else employee
            )
        else:
            st.metric("❌ Failed", "0")
            st.metric("👤 Employee", "None")

    if st.session_state.analysis_results:
        st.markdown("**Quick Actions:**")
        if st.button(
            "🔍 View Results", use_container_width=True, key="sidebar_view_results"
        ):
            st.session_state.selected_page = "📄 Invoice Analysis"
            st.rerun()
        if st.button("💭 Ask Questions", use_container_width=True, key="sidebar_chat"):
            st.session_state.selected_page = "💬 Chat with Invoices"
            st.rerun()

    st.markdown("---")

    if st.button(
        "🔄 Reset Session",
        type="secondary",
        use_container_width=True,
        key="reset_session_btn",
    ):
        st.session_state.analysis_results = None
        st.session_state.chat_history = []
        st.session_state.chat_session_id = str(uuid.uuid4())
        st.rerun()

    if (
        "analysis_in_progress" in st.session_state
        and st.session_state.analysis_in_progress
    ):
        st.info("🔄 Analysis in progress...")
        st.progress(st.session_state.get("analysis_progress", 0.0))

try:
    if selected_page in pages:
        pages[selected_page].main()
    else:
        st.error(f"Page '{selected_page}' not found!")
        st.info("Available pages: " + ", ".join(pages.keys()))
except Exception as e:
    st.error(f"Error running page: {e}")
    if st.checkbox("Show detailed error information"):
        st.exception(e)

    st.subheader("🔧 Troubleshooting")
    st.info("This error might be caused by:")
    st.write("• Backend service not running (FastAPI server on port 8000)")
    st.write("• Missing dependencies or configuration issues")
    st.write("• Network connectivity problems")

    if st.button("🔄 Retry", type="primary", key="retry_btn"):
        st.rerun()
