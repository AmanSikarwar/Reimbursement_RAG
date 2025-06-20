#!/usr/bin/env python3
"""
Advanced Streaming Client for Invoice Analysis Endpoint.

This script demonstrates how to consume the streaming invoice analysis endpoint
using Server-Sent Events (SSE) with file uploads and real-time progress monitoring.
"""

import asyncio
import json
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import aiohttp


class StreamingInvoiceAnalysisClient:
    """
    Client for consuming streaming invoice analysis responses.

    This client demonstrates how to upload files and handle streaming
    responses from the invoice analysis endpoint.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the streaming invoice analysis client.

        Args:
            base_url: Base URL of the FastAPI server
        """
        self.base_url = base_url
        self.stream_url = f"{base_url}/api/v1/analyze-invoices-stream"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=600, connect=30
            )  # 10 min total for processing
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def create_sample_policy_pdf(self) -> bytes:
        """Create sample HR policy content as bytes."""
        policy_content = """
        COMPANY HR REIMBURSEMENT POLICY

        1. TRANSPORTATION EXPENSES
        - Taxi/Cab expenses: Maximum ₹500 per trip
        - Public transport: Actual cost with receipts
        - Personal vehicle: ₹8 per kilometer
        - Airport transfers: Up to ₹1000

        2. MEAL AND ENTERTAINMENT
        - Business meals: Up to ₹1000 per person
        - Client entertainment: Requires pre-approval
        - Team lunch: Up to ₹2000 per team event
        - Alcohol expenses: Not reimbursable

        3. OFFICE SUPPLIES AND EQUIPMENT
        - Stationery and supplies: Up to ₹5000 per month
        - Software subscriptions: Requires approval
        - Hardware/equipment: Pre-approval for items above ₹10000
        - Books and training materials: Up to ₹3000 per quarter

        4. ACCOMMODATION
        - Business travel accommodation: Actual cost with receipts
        - Maximum per night: ₹5000 for domestic travel
        - Hotel meals: Included in accommodation reimbursement

        5. GENERAL RULES
        - All expenses must have valid receipts/invoices
        - Expenses must be submitted within 30 days
        - Personal expenses are not reimbursable
        - Receipts must be clear and legible
        - Employee signature required on expense reports
        """
        return policy_content.encode("utf-8")

    def create_sample_invoices_zip(self) -> bytes:
        """Create a ZIP file with sample invoice PDFs."""
        invoices_data = [
            {
                "filename": "taxi_receipt.pdf",
                "content": """
                METRO TAXI SERVICES
                Invoice #: TX-2024-0615-001
                Date: June 15, 2024
                
                Customer: John Doe
                Trip Details:
                - From: Corporate Office, Sector 62, Noida
                - To: Indira Gandhi International Airport, Delhi
                - Distance: 28 km
                - Duration: 45 minutes
                
                Fare Breakdown:
                - Base fare: ₹350
                - Distance charge: ₹84 (28 km × ₹3/km)
                - Time charge: ₹15
                - Service tax: ₹45
                
                TOTAL AMOUNT: ₹494
                Payment Method: Cash
                Driver: Rajesh Kumar (License: DL-123456)
                """,
            },
            {
                "filename": "business_lunch.pdf",
                "content": """
                CORPORATE DINING RESTAURANT
                GST Invoice #: CD-2024-0614-089
                Date: June 14, 2024
                Time: 1:30 PM
                
                Customer: John Doe
                Party Size: 3 persons
                Occasion: Client meeting with ABC Corp
                
                Order Details:
                - Executive Lunch Set × 3: ₹1,800
                - Fresh Juice × 3: ₹450
                - Coffee × 2: ₹200
                - Dessert × 3: ₹450
                
                Subtotal: ₹2,900
                Service Charge (10%): ₹290
                GST (18%): ₹574.2
                
                TOTAL AMOUNT: ₹3,764.20
                Payment Method: Corporate Credit Card
                GSTIN: 07AABCD1234E1ZW
                """,
            },
            {
                "filename": "office_supplies.pdf",
                "content": """
                OFFICEMAX SOLUTIONS PVT LTD
                Tax Invoice #: OMS-2024-0613-156
                Date: June 13, 2024
                
                Bill To: John Doe
                Department: IT Development
                
                Items Purchased:
                1. Wireless Ergonomic Mouse: ₹1,200
                2. Mechanical Keyboard: ₹2,500  
                3. Laptop Stand Adjustable: ₹1,800
                4. USB-C Hub 7-in-1: ₹2,200
                5. Webcam HD 1080p: ₹1,500
                
                Subtotal: ₹9,200
                Discount (5%): -₹460
                GST (18%): ₹1,573.20
                
                TOTAL AMOUNT: ₹10,313.20
                Payment Terms: Net 30 days
                GSTIN: 09AABCO1234P1ZV
                """,
            },
            {
                "filename": "hotel_accommodation.pdf",
                "content": """
                BUSINESS HOTEL GRAND
                Invoice #: BHG-2024-0612-078
                Check-in: June 12, 2024 (2:00 PM)
                Check-out: June 13, 2024 (11:00 AM)
                
                Guest: John Doe
                Room: Deluxe Business Suite #501
                Nights: 1
                
                Charges:
                - Room Rate (1 night): ₹4,500
                - Breakfast: ₹500
                - WiFi: Complimentary
                - Business Center: ₹100
                - Service Tax (18%): ₹918
                
                TOTAL AMOUNT: ₹6,018
                Payment Method: Corporate Account
                Guest Signature: [Signed]
                """,
            },
            {
                "filename": "personal_expense.pdf",
                "content": """
                FASHION STORE DELUXE
                Receipt #: FSD-2024-0610-234
                Date: June 10, 2024
                
                Customer: John Doe
                
                Items:
                - Designer Shirt: ₹2,500
                - Formal Trousers: ₹3,200
                - Leather Belt: ₹1,800
                - Dress Shoes: ₹4,500
                
                Subtotal: ₹12,000
                GST (12%): ₹1,440
                
                TOTAL AMOUNT: ₹13,440
                Payment: Personal Credit Card
                
                Note: Personal shopping for wardrobe
                """,
            },
        ]

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for invoice in invoices_data:
                zip_file.writestr(
                    invoice["filename"], invoice["content"].encode("utf-8")
                )

        return zip_buffer.getvalue()

    async def analyze_invoices_streaming(self, employee_name: str = "John Doe"):
        """
        Stream invoice analysis with sample files.

        Args:
            employee_name: Name of the employee

        Returns:
            Dictionary containing the complete response and metadata
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        print(f"🚀 Starting streaming invoice analysis for: {employee_name}")
        print(f"📡 Endpoint: {self.stream_url}")

        # Create sample files
        policy_content = self.create_sample_policy_pdf()
        invoices_zip_content = self.create_sample_invoices_zip()

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as policy_file:
            policy_file.write(policy_content)
            policy_file_path = policy_file.name

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as zip_file:
            zip_file.write(invoices_zip_content)
            zip_file_path = zip_file.name

        start_time = time.time()
        response_data = {
            "metadata": {},
            "progress_updates": [],
            "invoice_results": [],
            "errors": [],
            "chunks_received": 0,
            "processing_stages": set(),
        }

        try:
            # Prepare multipart form data
            with open(policy_file_path, "rb") as pf, open(zip_file_path, "rb") as zf:
                form_data = aiohttp.FormData()
                form_data.add_field("employee_name", employee_name)
                form_data.add_field(
                    "policy_file",
                    pf,
                    filename="hr_policy.pdf",
                    content_type="application/pdf",
                )
                form_data.add_field(
                    "invoices_zip",
                    zf,
                    filename="invoices.zip",
                    content_type="application/zip",
                )

                async with self.session.post(
                    self.stream_url,
                    data=form_data,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")

                    print(f"✅ Connection established (HTTP {response.status})")
                    print("📦 Processing invoices...")

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
                                chunk_payload = chunk.get("data", {})
                                response_data["processing_stages"].add(chunk_type)

                                if chunk_type == "metadata":
                                    response_data["metadata"] = chunk_payload
                                    employee = chunk_payload.get("employee", "Unknown")
                                    print(f"📊 Metadata: Processing for {employee}")

                                elif chunk_type == "policy_processing":
                                    status = chunk_payload.get("status")
                                    if status == "extracting_policy":
                                        print("📄 Extracting policy text...")
                                    elif status == "completed":
                                        policy_length = chunk_payload.get(
                                            "policy_length", 0
                                        )
                                        print(
                                            f"✅ Policy processed ({policy_length} characters)"
                                        )

                                elif chunk_type == "progress":
                                    response_data["progress_updates"].append(
                                        chunk_payload
                                    )
                                    current = chunk_payload.get("current_invoice", 0)
                                    total = chunk_payload.get("total_invoices", 0)
                                    filename = chunk_payload.get("current_filename", "")
                                    stage = chunk_payload.get("stage", "")
                                    print(
                                        f"📈 Progress: {current}/{total} - {filename} ({stage})"
                                    )

                                elif chunk_type == "invoice_extraction":
                                    filename = chunk_payload.get("filename", "")
                                    status = chunk_payload.get("status", "")
                                    if status == "extracting":
                                        print(f"📄 Extracting text from {filename}...")
                                    elif status == "completed":
                                        text_length = chunk_payload.get(
                                            "text_length", 0
                                        )
                                        print(
                                            f"✅ Text extracted from {filename} ({text_length} chars)"
                                        )

                                elif chunk_type == "invoice_analysis":
                                    filename = chunk_payload.get("filename", "")
                                    status = chunk_payload.get("status", "")
                                    if status == "starting":
                                        print(f"🔍 Starting analysis of {filename}...")
                                    elif status == "analyzing":
                                        stage = chunk_payload.get("stage", "")
                                        print(f"🤖 Analyzing {filename} ({stage})...")
                                    elif status == "completed":
                                        result = chunk_payload.get("result", {})
                                        result_status = result.get("status", "unknown")
                                        amount = result.get("total_amount", 0)
                                        print(
                                            f"✅ Analysis completed: {filename} - {result_status} (₹{amount})"
                                        )

                                elif chunk_type == "vector_storage":
                                    filename = chunk_payload.get("filename", "")
                                    status = chunk_payload.get("status", "")
                                    if status == "storing":
                                        print(
                                            f"💾 Storing {filename} in vector database..."
                                        )
                                    elif status == "completed":
                                        print(
                                            f"✅ Stored {filename} in vector database"
                                        )

                                elif chunk_type == "result":
                                    response_data["invoice_results"].append(
                                        chunk_payload
                                    )
                                    filename = chunk_payload.get("filename", "")
                                    status = chunk_payload.get("status", "")
                                    amount = chunk_payload.get("total_amount", 0)
                                    reimbursement = chunk_payload.get(
                                        "reimbursement_amount", 0
                                    )
                                    print(
                                        f"📋 Result: {filename} - {status} (₹{amount} → ₹{reimbursement})"
                                    )

                                elif chunk_type == "error":
                                    error_msg = chunk_payload.get(
                                        "error", "Unknown error"
                                    )
                                    filename = chunk_payload.get("file", "Unknown file")
                                    response_data["errors"].append(chunk_payload)
                                    print(
                                        f"❌ Error processing {filename}: {error_msg}"
                                    )

                                elif chunk_type == "done":
                                    total_time = time.time() - start_time
                                    processed = chunk_payload.get(
                                        "processed_invoices", 0
                                    )
                                    failed = chunk_payload.get("failed_invoices", 0)

                                    print("\n🎉 Processing completed!")
                                    print(f"⏱️  Total time: {total_time:.2f}s")
                                    print(
                                        f"📊 Results: {processed} processed, {failed} failed"
                                    )

                                    response_data["final_summary"] = chunk_payload
                                    break

                            except json.JSONDecodeError as e:
                                print(f"\n⚠️  Invalid JSON in chunk: {e}")
                                response_data["errors"].append(
                                    f"JSON decode error: {e}"
                                )
                                continue

        except Exception as e:
            error_msg = f"Streaming error: {str(e)}"
            print(f"\n❌ {error_msg}")
            response_data["errors"].append(error_msg)

        finally:
            # Clean up temporary files
            try:
                Path(policy_file_path).unlink()
                Path(zip_file_path).unlink()
            except Exception:
                pass

        return response_data

    def print_analysis_summary(self, response_data):
        """Print a formatted summary of the analysis results."""
        print("\n" + "=" * 60)
        print("📊 STREAMING INVOICE ANALYSIS SUMMARY")
        print("=" * 60)

        # Processing summary
        print(f"📦 Chunks received: {response_data['chunks_received']}")
        print(
            f"🔄 Processing stages: {', '.join(sorted(response_data['processing_stages']))}"
        )

        # Invoice results summary
        results = response_data.get("invoice_results", [])
        if results:
            print(f"\n📋 Invoice Results ({len(results)} invoices):")
            total_amount = 0
            total_reimbursement = 0

            for i, result in enumerate(results, 1):
                filename = result.get("filename", "Unknown")
                status = result.get("status", "unknown")
                amount = result.get("total_amount", 0)
                reimbursement = result.get("reimbursement_amount", 0)
                currency = result.get("currency", "INR")

                total_amount += amount
                total_reimbursement += reimbursement

                print(f"   {i}. {filename}")
                print(f"      Status: {status}")
                print(
                    f"      Amount: {currency} {amount:.2f} → {currency} {reimbursement:.2f}"
                )

                violations = result.get("policy_violations")
                if violations:
                    print(f"      Violations: {', '.join(violations)}")
                print()

            print(f"💰 Total Amount: INR {total_amount:.2f}")
            print(f"💸 Total Reimbursement: INR {total_reimbursement:.2f}")
            print(
                f"📊 Reimbursement Rate: {(total_reimbursement / total_amount * 100) if total_amount > 0 else 0:.1f}%"
            )

        # Error summary
        errors = response_data.get("errors", [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                if isinstance(error, dict):
                    filename = error.get("file", "Unknown")
                    error_msg = error.get("error", "Unknown error")
                    print(f"   {i}. {filename}: {error_msg}")
                else:
                    print(f"   {i}. {error}")
        else:
            print("\n✅ No errors encountered")


async def main():
    """Main function demonstrating streaming invoice analysis."""
    print("🧪 Invoice Reimbursement System - Streaming Analysis Demo")
    print("=" * 60)

    async with StreamingInvoiceAnalysisClient() as client:
        try:
            print("📋 Creating sample invoice files:")
            print("   • HR reimbursement policy PDF")
            print("   • ZIP file with 5 sample invoices:")
            print("     - Taxi receipt (₹494)")
            print("     - Business lunch (₹3,764)")
            print("     - Office supplies (₹10,313)")
            print("     - Hotel accommodation (₹6,018)")
            print("     - Personal expense (₹13,440) [should be declined]")
            print()

            response = await client.analyze_invoices_streaming("John Doe")
            client.print_analysis_summary(response)

        except Exception as e:
            print(f"❌ Demo failed: {e}")

    print("\n🎉 Streaming invoice analysis demo completed!")


if __name__ == "__main__":
    print("📌 Make sure the FastAPI server is running on http://localhost:8000")
    print("   Start it with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
