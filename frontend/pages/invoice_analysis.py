"""
Invoice Analysis Page for Streamlit Frontend

This page handles the invoice analysis functionality with real-time streaming
updates from the backend API.
"""

import json
import time
from typing import Any, Dict

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


def stream_analysis(employee_name: str, policy_file, invoices_zip) -> Dict[str, Any]:
    """
    Stream invoice analysis with real-time updates.

    Args:
        employee_name: Name of the employee
        policy_file: Uploaded policy PDF file
        invoices_zip: Uploaded invoices ZIP file

    Returns:
        Dictionary containing analysis results and metadata
    """
    api_url = "http://localhost:8000/api/v1/analyze-invoices-stream"

    # Prepare files for upload
    files = {
        "policy_file": (policy_file.name, policy_file.getvalue(), "application/pdf"),
        "invoices_zip": (invoices_zip.name, invoices_zip.getvalue(), "application/zip"),
    }
    data = {"employee_name": employee_name}

    # Initialize response data
    response_data = {
        "metadata": {},
        "progress_updates": [],
        "invoice_results": [],
        "errors": [],
        "chunks_received": 0,
        "processing_stages": set(),
        "final_summary": {},
    }

    # Create containers for real-time updates
    status_container = st.container()
    progress_container = st.container()
    individual_results_container = st.container()

    with status_container:
        status_placeholder = st.empty()

    with progress_container:
        progress_placeholder = st.empty()
        progress_bar = st.progress(0)

    with individual_results_container:
        st.subheader("Invoice Results")
        individual_results_placeholder = st.empty()

    # Store individual results for immediate display
    individual_results = []

    start_time = time.time()

    try:
        with httpx.stream(
            "POST", api_url, files=files, data=data, timeout=600.0
        ) as response:
            if response.status_code != 200:
                error_text = response.text
                st.error(f"❌ HTTP {response.status_code}: {error_text}")
                return response_data

            status_placeholder.success("✅ Connected to backend - Starting analysis...")

            for line in response.iter_lines():
                if line.startswith("data:"):
                    try:
                        chunk_data = line[5:]
                        if not chunk_data.strip():
                            continue

                        # Enhanced error detection for service unavailable errors
                        if (
                            "503 Service Unavailable" in chunk_data
                            or "The model is overloaded" in chunk_data
                        ):
                            st.error("🚫 AI Service Temporarily Unavailable")
                            st.warning(
                                "The AI analysis service is currently overloaded. Please try again in a few minutes."
                            )
                            response_data["errors"].append(
                                "Service temporarily unavailable - model overloaded"
                            )
                            continue

                        # Check for other HTTP error patterns
                        if chunk_data.startswith("Error:") and (
                            "Service Unavailable" in chunk_data
                            or "UNAVAILABLE" in chunk_data
                        ):
                            st.error("🚫 Backend Service Error")
                            st.warning(
                                "The analysis service is experiencing issues. Please try again later."
                            )
                            response_data["errors"].append(
                                f"Backend error: {chunk_data[:100]}..."
                            )
                            continue

                        # Try to parse as JSON
                        chunk = json.loads(chunk_data)
                        response_data["chunks_received"] += 1

                        chunk_type = chunk.get("type")
                        chunk_payload = chunk.get("data", {})
                        response_data["processing_stages"].add(chunk_type)

                        # Handle different chunk types
                        if chunk_type == "metadata":
                            response_data["metadata"] = chunk_payload
                            employee = chunk_payload.get("employee", "Unknown")
                            status_placeholder.info(f"Starting analysis for {employee}")

                        elif chunk_type == "policy_processing":
                            status = chunk_payload.get("status")
                            if status == "extracting_policy":
                                status_placeholder.info(
                                    "📄 Extracting HR policy text..."
                                )
                            elif status == "completed":
                                policy_length = chunk_payload.get("policy_length", 0)
                                status_placeholder.success(
                                    f"✅ Policy processed ({policy_length:,} characters)"
                                )

                        elif chunk_type == "progress":
                            response_data["progress_updates"].append(chunk_payload)
                            current = chunk_payload.get("current_invoice", 0)
                            total = chunk_payload.get("total_invoices", 0)
                            filename = chunk_payload.get("current_filename", "")
                            stage = chunk_payload.get("stage", "")

                            if total > 0:
                                progress_value = current / total
                                progress_bar.progress(progress_value)
                                progress_placeholder.info(
                                    f"📈 Processing {current}/{total}: {filename} ({stage})"
                                )

                                # Update session state progress
                                st.session_state.analysis_progress = progress_value

                        elif chunk_type == "invoice_extraction":
                            filename = chunk_payload.get("filename", "")
                            status = chunk_payload.get("status", "")
                            if status == "extracting":
                                status_placeholder.info(
                                    f"📄 Extracting text from {filename}..."
                                )
                            elif status == "completed":
                                text_length = chunk_payload.get("text_length", 0)
                                status_placeholder.success(
                                    f"✅ Text extracted from {filename} ({text_length:,} characters)"
                                )

                        elif chunk_type == "invoice_analysis":
                            filename = chunk_payload.get("filename", "")
                            status = chunk_payload.get("status", "")
                            if status == "starting":
                                status_placeholder.info(
                                    f"🔍 Starting analysis of {filename}..."
                                )
                            elif status == "analyzing":
                                stage = chunk_payload.get("stage", "")
                                status_placeholder.info(
                                    f"🤖 Analyzing {filename} ({stage})..."
                                )
                            elif status == "completed":
                                result = chunk_payload.get("result", {})
                                result_status = result.get("status", "unknown")
                                amount = result.get("total_amount", 0)
                                status_placeholder.success(
                                    f"✅ Analysis completed: {filename} - {result_status} ({format_currency(amount)})"
                                )

                        elif chunk_type == "vector_storage":
                            filename = chunk_payload.get("filename", "")
                            status = chunk_payload.get("status", "")
                            if status == "storing":
                                status_placeholder.info(
                                    f"💾 Storing {filename} in vector database..."
                                )
                            elif status == "completed":
                                status_placeholder.success(
                                    f"✅ Stored {filename} in vector database"
                                )

                        elif chunk_type == "result":
                            response_data["invoice_results"].append(chunk_payload)
                            individual_results.append(chunk_payload)

                            # Display individual result immediately
                            with individual_results_placeholder.container():
                                display_individual_results(individual_results)

                        elif chunk_type == "error":
                            error_msg = chunk_payload.get("error", "Unknown error")
                            filename = chunk_payload.get("file", "Unknown file")
                            response_data["errors"].append(chunk_payload)

                            # Enhanced error message handling
                            if (
                                "parsing analysis" in error_msg
                                and "503 Service Unavailable" in error_msg
                            ):
                                st.error(f"🚫 AI Service Unavailable for {filename}")
                                st.info(
                                    "💡 The AI analysis service is temporarily overloaded. This file will be skipped."
                                )
                            elif "overloaded" in error_msg.lower():
                                st.error(f"⏳ Service Overloaded for {filename}")
                                st.info(
                                    "💡 Please try again later when the service is less busy."
                                )
                            else:
                                st.error(f"❌ Error processing {filename}: {error_msg}")

                        elif chunk_type == "done":
                            total_time = time.time() - start_time
                            processed = chunk_payload.get("processed_invoices", 0)
                            failed = chunk_payload.get("failed_invoices", 0)

                            progress_bar.progress(1.0)
                            status_placeholder.success(
                                f"🎉 Processing completed in {total_time:.2f}s!"
                            )
                            progress_placeholder.success(
                                f"📊 Results: {processed} processed, {failed} failed"
                            )

                            response_data["final_summary"] = chunk_payload
                            break

                    except json.JSONDecodeError as e:
                        # Enhanced JSON parsing error handling
                        if (
                            "503 Service Unavailable" in chunk_data
                            or "overloaded" in chunk_data
                        ):
                            st.warning("⚠️ AI Service Temporarily Overloaded")
                            st.info(
                                "💡 Skipping malformed response due to service overload. Processing will continue."
                            )
                            response_data["errors"].append(
                                "Service overload caused parsing error"
                            )
                        else:
                            # Log the parsing error but don't show to user unless it's critical
                            response_data["errors"].append(
                                f"JSON parsing error: {str(e)[:100]}..."
                            )
                        continue  # Skip malformed JSON
                    except Exception as e:
                        # Catch any other unexpected errors in chunk processing
                        st.warning(f"⚠️ Unexpected error processing chunk: {str(e)}")
                        response_data["errors"].append(
                            f"Chunk processing error: {str(e)}"
                        )
                        continue

    except httpx.TimeoutException:
        st.error("⏰ Request Timeout")
        st.warning(
            "The analysis is taking longer than expected. Please try again with fewer files or check your internet connection."
        )
        response_data["errors"].append("Request timeout - analysis took too long")
    except httpx.ConnectError:
        st.error("🔌 Connection Error")
        st.warning(
            "Unable to connect to the backend service. Please ensure the FastAPI server is running."
        )
        response_data["errors"].append("Connection error - backend service unavailable")
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "overloaded" in error_msg.lower():
            st.error("🚫 AI Service Temporarily Unavailable")
            st.warning(
                "The AI analysis service is currently overloaded. Please try again in a few minutes."
            )
            st.info("💡 Tip: Try processing fewer invoices at once to reduce load.")
        elif "timeout" in error_msg.lower():
            st.error("⏰ Operation Timed Out")
            st.warning(
                "The analysis took too long to complete. Please try again with fewer files."
            )
        else:
            st.error(f"❌ Unexpected error: {error_msg}")
            st.info("💡 Please try again. If the problem persists, contact support.")
        response_data["errors"].append(f"Streaming error: {error_msg}")

    return response_data


def display_results(response_data: Dict[str, Any]):
    """Display the final analysis results in a formatted way."""

    # Summary metrics
    final_summary = response_data.get("final_summary", {})
    if final_summary:
        st.subheader("Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Invoices", final_summary.get("total_invoices", 0))
        with col2:
            st.metric("Processed", final_summary.get("processed_invoices", 0))
        with col3:
            st.metric("Failed", final_summary.get("failed_invoices", 0))
        with col4:
            processing_time = final_summary.get("processing_time_seconds", 0)
            st.metric("Processing Time", f"{processing_time:.1f}s")

    # Detailed results
    results = response_data.get("invoice_results", [])
    if results:
        st.subheader("📋 Detailed Results")

        # Calculate totals
        total_amount = sum(result.get("total_amount", 0) for result in results)
        total_reimbursement = sum(
            result.get("reimbursement_amount", 0) for result in results
        )
        reimbursement_rate = (
            (total_reimbursement / total_amount * 100) if total_amount > 0 else 0
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Amount", format_currency(total_amount))
        with col2:
            st.metric("Total Reimbursement", format_currency(total_reimbursement))
        with col3:
            st.metric("Reimbursement Rate", f"{reimbursement_rate:.1f}%")

        # Individual results
        for i, result in enumerate(results, 1):
            with st.expander(
                f"{get_status_icon(result.get('status', ''))} {result.get('filename', 'Unknown')}"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        "**Status:**",
                        result.get("status", "unknown").replace("_", " ").title(),
                    )
                    st.write(
                        "**Total Amount:**",
                        format_currency(
                            result.get("total_amount", 0), result.get("currency", "INR")
                        ),
                    )
                    st.write(
                        "**Reimbursement:**",
                        format_currency(
                            result.get("reimbursement_amount", 0),
                            result.get("currency", "INR"),
                        ),
                    )

                with col2:
                    if result.get("categories"):
                        st.write(
                            "**Categories:**",
                            ", ".join(result.get("categories", [])).title(),
                        )

                    if result.get("policy_violations"):
                        st.write("**Policy Violations:**")
                        for violation in result.get("policy_violations", []):
                            st.write(f"- {violation}")

                st.write("**Reason:**", result.get("reason", "No reason provided"))

    # Error summary with enhanced messaging
    errors = response_data.get("errors", [])
    if errors:
        # Categorize errors
        service_errors = []
        parsing_errors = []
        timeout_errors = []
        other_errors = []

        for error in errors:
            error_text = (
                error if isinstance(error, str) else error.get("error", "Unknown error")
            )

            if (
                "overloaded" in error_text.lower()
                or "503" in error_text
                or "unavailable" in error_text.lower()
            ):
                service_errors.append(error)
            elif "parsing" in error_text.lower() or "json" in error_text.lower():
                parsing_errors.append(error)
            elif "timeout" in error_text.lower():
                timeout_errors.append(error)
            else:
                other_errors.append(error)

        # Display categorized errors
        with st.expander(f"⚠️ Issues Encountered ({len(errors)})", expanded=False):
            if service_errors:
                st.subheader("🚫 AI Service Issues")
                st.warning(
                    "The AI analysis service was temporarily overloaded during processing."
                )
                st.info(
                    "💡 **Recommendation**: Try again in a few minutes, or process fewer invoices at once."
                )
                for i, error in enumerate(service_errors, 1):
                    if isinstance(error, dict):
                        filename = error.get("file", "Service")
                        st.write(
                            f"{i}. **{filename}**: Service temporarily unavailable"
                        )
                    else:
                        st.write(f"{i}. Service overload issue")
                st.markdown("---")

            if parsing_errors:
                st.subheader("📄 Data Processing Issues")
                st.info(
                    "Some responses couldn't be properly processed due to service instability."
                )
                for i, error in enumerate(parsing_errors, 1):
                    if isinstance(error, dict):
                        filename = error.get("file", "Unknown")
                        st.write(f"{i}. **{filename}**: Data processing error")
                    else:
                        st.write(f"{i}. Response parsing issue")
                st.markdown("---")

            if timeout_errors:
                st.subheader("⏰ Timeout Issues")
                st.info("Some operations took longer than expected to complete.")
                for i, error in enumerate(timeout_errors, 1):
                    if isinstance(error, dict):
                        filename = error.get("file", "Unknown")
                        st.write(f"{i}. **{filename}**: Processing timeout")
                    else:
                        st.write(f"{i}. Operation timeout")
                st.markdown("---")

            if other_errors:
                st.subheader("🔧 Other Issues")
                for i, error in enumerate(other_errors, 1):
                    if isinstance(error, dict):
                        filename = error.get("file", "Unknown")
                        error_msg = error.get("error", "Unknown error")
                        st.write(f"{i}. **{filename}**: {error_msg}")
                    else:
                        st.write(f"{i}. {error}")

            st.info("💡 **General Tips**:")
            st.write("• If you see service overload errors, try again in 5-10 minutes")
            st.write("• For best results, process 5-10 invoices at a time")
            st.write("• Ensure your PDF files are not corrupted or password-protected")
            st.write("• Check that your internet connection is stable")


def display_individual_results(results):
    """Display individual invoice results as they are processed."""
    if not results:
        return

    # Create a table for the results
    for i, result in enumerate(results):
        filename = result.get("filename", "Unknown")
        status = result.get("status", "unknown")
        total_amount = result.get("total_amount", 0)
        reimbursement_amount = result.get("reimbursement_amount", 0)
        currency = result.get("currency", "INR")
        reason = result.get("reason", "")

        # Create expandable section for each result
        with st.expander(
            f"{get_status_icon(status)} {filename} - {status.replace('_', ' ').title()}",
            expanded=i == len(results) - 1,
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Status", status.replace("_", " ").title())
            with col2:
                st.metric("Total Amount", format_currency(total_amount, currency))
            with col3:
                st.metric(
                    "Reimbursement", format_currency(reimbursement_amount, currency)
                )

            if reason:
                st.write("**Reason:**")
                st.write(reason)

            # Show policy violations if any
            violations = result.get("policy_violations", [])
            if violations:
                st.write("**Policy Violations:**")
                for violation in violations:
                    st.write(f"• {violation}")

            # Show categories if any
            categories = result.get("categories", [])
            if categories:
                st.write("**Categories:** " + ", ".join(categories).title())


def main():
    """Main function for the Invoice Analysis page."""

    # Enhanced header with iAI branding
    st.title("📄 Automated Invoice Analysis")
    st.subheader("AI-powered invoice processing and reimbursement analysis")

    # Show system status at the top if backend is offline
    from utils.streamlit_utils import check_backend_health

    health_status = check_backend_health()
    if health_status["status"] != "online":
        st.warning(f"⚠️ Backend Status: {health_status['message']}")
        with st.expander("🔧 Backend Setup Instructions", expanded=False):
            st.info(
                "To use this application, you need to start the FastAPI backend server:"
            )
            st.code(
                "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
            )
            st.info(
                "The backend provides the AI analysis capabilities for processing invoices."
            )

    # Header with navigation hint
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.session_state.analysis_results:
            if st.button(
                "💬 Chat with Results", type="primary", use_container_width=True
            ):
                st.session_state.selected_page = "💬 Chat with Invoices"
                st.rerun()

    # Status indicator with standard metrics
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Status", "✅ Completed")
        with col2:
            st.metric("📋 Processed", results.get("processed_invoices", 0))
        with col3:
            st.metric("❌ Failed", results.get("failed_invoices", 0))

        # Quick actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(
                "🔄 New Analysis", use_container_width=True, key="new_analysis_btn"
            ):
                st.session_state.analysis_results = None
                st.rerun()
        with col2:
            if st.button(
                "📊 View Detailed Results",
                use_container_width=True,
                key="view_results_btn",
            ):
                st.session_state.show_detailed_results = True
                st.rerun()
        with col3:
            if st.button(
                "💬 Start Chatting", use_container_width=True, key="start_chat_btn"
            ):
                st.session_state.selected_page = "💬 Chat with Invoices"
                st.rerun()

        st.markdown("---")

    # Input form
    if not st.session_state.analysis_results:
        # Welcome section for new users
        if not st.session_state.get("show_upload_form", False):
            st.markdown("---")
            st.subheader("🎯 Welcome to AI Invoice Analysis")

            st.markdown("""
            This application uses **advanced AI technology** to automatically analyze invoice reimbursement requests 
            against your company's HR policies. Here's what it does:
            
            **✨ Key Features:**
            - 📄 **Smart PDF Processing**: Extracts text from invoices and policy documents
            - 🤖 **AI Analysis**: Uses Gemini AI to analyze each invoice against HR policies  
            - 💰 **Automatic Calculations**: Determines reimbursement amounts and policy compliance
            - 💬 **Interactive Chat**: Ask questions about your processed invoices using natural language
            - 📊 **Detailed Reports**: Get comprehensive analysis results with explanations
            """)

            col1, col2 = st.columns(2)
            with col1:
                st.info(
                    "**📋 What You Need:**\n• Employee name\n• HR policy PDF file\n• ZIP file with invoice PDFs"
                )
            with col2:
                st.success(
                    "**🎉 What You Get:**\n• Automated analysis results\n• Reimbursement calculations\n• Policy violation reports"
                )

            st.markdown("---")

            # Get started button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "🚀 Get Started - Upload Documents",
                    type="primary",
                    use_container_width=True,
                    key="get_started_btn",
                ):
                    st.session_state.show_upload_form = True
                    st.rerun()

        # Upload form (shown after clicking get started or if already set to show)
        if st.session_state.get("show_upload_form", False):
            st.subheader("📝 Analysis Configuration")

            # Employee name input
            employee_name = st.text_input(
                "Employee Name *",
                placeholder="Enter the employee's full name",
                help="Name of the employee whose invoices are being analyzed",
                key="employee_name_input",
            )

            # Initialize session state for file uploads
            if "uploaded_policy" not in st.session_state:
                st.session_state.uploaded_policy = None
            if "uploaded_zip" not in st.session_state:
                st.session_state.uploaded_zip = None

            col1, col2 = st.columns(2)

            with col1:
                # Policy file uploader
                policy_file = st.file_uploader(
                    "HR Policy File *",
                    type=["pdf"],
                    help="Upload the HR reimbursement policy PDF file",
                    key="policy_uploader",
                )
                # Update session state when file is uploaded
                if policy_file is not None:
                    st.session_state.uploaded_policy = policy_file

            with col2:
                # Invoices zip uploader
                invoices_zip = st.file_uploader(
                    "Invoices ZIP File *",
                    type=["zip"],
                    help="Upload a ZIP file containing all invoice PDFs",
                    key="zip_uploader",
                )
                # Update session state when file is uploaded
                if invoices_zip is not None:
                    st.session_state.uploaded_zip = invoices_zip

            # Simple, reliable validation - try multiple approaches
            name_valid = employee_name and len(employee_name.strip()) > 0

            # Check file uploads - try different validation methods
            policy_valid = False
            zip_valid = False

            if policy_file is not None:
                policy_valid = True
                active_policy_file = policy_file
            elif st.session_state.uploaded_policy is not None:
                policy_valid = True
                active_policy_file = st.session_state.uploaded_policy
            else:
                active_policy_file = None

            if invoices_zip is not None:
                zip_valid = True
                active_zip_file = invoices_zip
            elif st.session_state.uploaded_zip is not None:
                zip_valid = True
                active_zip_file = st.session_state.uploaded_zip
            else:
                active_zip_file = None

            # Overall validation
            all_valid = name_valid and policy_valid and zip_valid

            # Show missing fields if any
            if not all_valid:
                missing_fields = []
                if not name_valid:
                    missing_fields.append("Employee Name")
                if not policy_valid:
                    missing_fields.append("HR Policy File")
                if not zip_valid:
                    missing_fields.append("Invoices ZIP File")

                if missing_fields:
                    st.info(f"ℹ️ Please provide: {', '.join(missing_fields)}")

            # Submit button
            if st.button(
                "🚀 Start Analysis",
                type="primary",
                disabled=not all_valid,
                use_container_width=True,
                key="start_analysis_btn",
            ):
                if all_valid:
                    st.info("🚀 Starting invoice analysis...")

                    # Set progress indicators
                    st.session_state.analysis_in_progress = True
                    st.session_state.analysis_progress = 0.0

                    # Stream the analysis using active files
                    response_data = stream_analysis(
                        employee_name, active_policy_file, active_zip_file
                    )

                    # Clear progress indicators
                    st.session_state.analysis_in_progress = False
                    st.session_state.analysis_progress = 1.0

                    # Store results in session state
                    st.session_state.analysis_results = {
                        "employee_name": employee_name,
                        "processed_invoices": len(
                            response_data.get("invoice_results", [])
                        ),
                        "failed_invoices": len(response_data.get("errors", [])),
                        "response_data": response_data,
                    }

                    # Clear uploaded files from session state
                    st.session_state.uploaded_policy = None
                    st.session_state.uploaded_zip = None

                    st.rerun()
                else:
                    st.error(
                        "❌ Please fill in all required fields before starting analysis."
                    )
        else:
            # Show a small hint for users who want to skip the intro
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "📋 Skip Intro - Go to Upload",
                    use_container_width=True,
                    key="skip_intro_btn",
                ):
                    st.session_state.show_upload_form = True
                    st.rerun()

    # Display results if available
    if st.session_state.analysis_results:
        st.markdown("---")
        response_data = st.session_state.analysis_results["response_data"]
        display_results(response_data)


if __name__ == "__main__":
    main()
