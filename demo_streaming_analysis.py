#!/usr/bin/env python3
"""
Simple demonstration of streaming invoice analysis endpoint.

This script shows how the streaming endpoint works by using pre-created test files.
"""

import asyncio
import json
import tempfile
import zipfile
from pathlib import Path

import aiohttp


async def test_streaming_endpoint():
    """Test the streaming invoice analysis endpoint with simple files."""

    print("🧪 Testing Streaming Invoice Analysis Endpoint")
    print("=" * 60)

    # Create simple test files
    print("📁 Creating test files...")

    # Create a simple policy file
    policy_content = """
HR REIMBURSEMENT POLICY

1. TRAVEL EXPENSES
- Maximum cab fare: ₹500 per trip
- Receipts required for all expenses

2. MEAL EXPENSES  
- Business meals: Up to ₹1000 per meal
- Alcohol not reimbursable

3. OFFICE SUPPLIES
- Up to ₹5000 per month for office supplies
"""

    # Create sample invoices
    invoice1 = (
        "TAXI RECEIPT\nDate: 2024-06-20\nAmount: ₹350\nDescription: Airport transfer"
    )
    invoice2 = "RESTAURANT BILL\nDate: 2024-06-20\nAmount: ₹800\nDescription: Business lunch with client"
    invoice3 = "OFFICE SUPPLIES\nDate: 2024-06-20\nAmount: ₹2500\nDescription: Stationery and equipment"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Save policy file
        policy_file = temp_path / "policy.txt"
        policy_file.write_text(policy_content)

        # Create ZIP with invoices
        zip_file = temp_path / "invoices.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("invoice1.txt", invoice1)
            zf.writestr("invoice2.txt", invoice2)
            zf.writestr("invoice3.txt", invoice3)

        print(f"✅ Created policy file: {policy_file}")
        print(f"✅ Created ZIP with 3 invoices: {zip_file}")

        # Test streaming endpoint
        print("\n🚀 Testing streaming endpoint...")

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("employee_name", "John Doe")

            # Add policy file
            with open(policy_file, "rb") as f:
                data.add_field(
                    "policy_file", f, filename="policy.txt", content_type="text/plain"
                )

                # Add ZIP file
                with open(zip_file, "rb") as zf:
                    data.add_field(
                        "invoices_zip",
                        zf,
                        filename="invoices.zip",
                        content_type="application/zip",
                    )

                    try:
                        url = "http://localhost:8000/api/v1/analyze-invoices-stream"
                        print(f"📡 Connecting to: {url}")

                        async with session.post(url, data=data) as response:
                            print(f"📊 Response status: {response.status}")

                            if response.status == 200:
                                print("✅ Connection successful! Streaming results...")
                                chunk_count = 0

                                async for line in response.content:
                                    line = line.decode("utf-8").strip()
                                    if line.startswith("data: "):
                                        chunk_count += 1
                                        data_str = line[6:]  # Remove 'data: ' prefix
                                        try:
                                            chunk_data = json.loads(data_str)
                                            chunk_type = chunk_data.get(
                                                "type", "unknown"
                                            )
                                            print(
                                                f"   📦 Chunk {chunk_count} [{chunk_type}]: {chunk_data.get('data', {})}"
                                            )
                                        except json.JSONDecodeError:
                                            print(
                                                f"   📦 Chunk {chunk_count}: {data_str}"
                                            )

                                print(
                                    f"\n✅ Streaming completed! Received {chunk_count} chunks"
                                )
                            else:
                                error_text = await response.text()
                                print(f"❌ Error {response.status}: {error_text}")

                    except Exception as e:
                        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(test_streaming_endpoint())
