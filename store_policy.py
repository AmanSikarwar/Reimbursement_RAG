#!/usr/bin/env python3
"""
Policy Document Storage Script.

This script stores HR reimbursement policy documents in the vector database
to provide context for the chatbot.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import VectorStoreService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def store_policy_document(policy_file_path: str):
    """
    Store a policy document in the vector database.

    Args:
        policy_file_path: Path to the policy PDF file
    """
    try:
        # Initialize services
        vector_store = VectorStoreService()
        await vector_store.initialize()

        pdf_processor = PDFProcessor()

        # Process the policy PDF
        logger.info(f"Processing policy document: {policy_file_path}")
        policy_text = await pdf_processor.extract_text(policy_file_path)

        if not policy_text.strip():
            logger.error("No text extracted from policy document")
            return False

        # Store in vector database
        policy_name = Path(policy_file_path).stem
        doc_id = await vector_store.store_policy_document(
            policy_text=policy_text, policy_name=policy_name, organization="Company"
        )

        logger.info(f"Successfully stored policy document with ID: {doc_id}")
        return True

    except Exception as e:
        logger.error(f"Error storing policy document: {e}", exc_info=True)
        return False


async def store_default_policy():
    """
    Store a default HR reimbursement policy if no file is provided.
    """
    try:
        # Initialize services
        vector_store = VectorStoreService()
        await vector_store.initialize()

        # Default HR Reimbursement Policy
        default_policy = """
HR REIMBURSEMENT POLICY

1. ELIGIBLE EXPENSES
   - Business travel expenses (flights, accommodation, meals)
   - Transportation costs (taxi, uber, public transport)
   - Office supplies and equipment
   - Client entertainment (within limits)
   - Professional development and training
   - Communication expenses (phone, internet for business use)

2. NON-REIMBURSABLE EXPENSES
   - Alcoholic beverages (except for approved client entertainment)
   - Personal expenses
   - Fines and penalties
   - Entertainment for personal purposes
   - Luxury items beyond business necessity

3. SPENDING LIMITS
   - Meals: $50 per day for domestic travel, $75 per day for international
   - Accommodation: Up to $200 per night domestic, $300 per night international
   - Transportation: Economy class for flights, reasonable taxi/uber costs
   - Office supplies: Up to $500 per month per employee

4. DOCUMENTATION REQUIREMENTS
   - Original receipts required for all expenses over $25
   - Business purpose must be clearly stated
   - All expenses must be submitted within 30 days
   - Manager approval required for expenses over $500

5. APPROVAL PROCESS
   - Expenses under $100: Automatic approval with valid receipt
   - Expenses $100-$500: Manager approval required
   - Expenses over $500: Senior management approval required
   - All international travel: Pre-approval required

6. PAYMENT PROCESSING
   - Approved reimbursements processed within 5-7 business days
   - Direct deposit to employee's registered bank account
   - Rejected expenses will be returned with explanation

7. POLICY VIOLATIONS
   - First violation: Warning and training
   - Repeated violations: Progressive disciplinary action
   - Fraudulent claims: Immediate termination and legal action
        """

        # Store in vector database
        doc_id = await vector_store.store_policy_document(
            policy_text=default_policy,
            policy_name="HR_Reimbursement_Policy_Default",
            organization="Company",
        )

        logger.info(f"Successfully stored default policy document with ID: {doc_id}")
        return True

    except Exception as e:
        logger.error(f"Error storing default policy: {e}", exc_info=True)
        return False


async def main():
    """Main function to store policy documents."""
    if len(sys.argv) > 1:
        # Store specific policy file
        policy_file = sys.argv[1]
        if not Path(policy_file).exists():
            logger.error(f"Policy file not found: {policy_file}")
            sys.exit(1)

        success = await store_policy_document(policy_file)
    else:
        # Store default policy
        logger.info("No policy file provided, storing default policy...")
        success = await store_default_policy()

    if success:
        logger.info("Policy storage completed successfully!")
        sys.exit(0)
    else:
        logger.error("Policy storage failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
