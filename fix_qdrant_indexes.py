#!/usr/bin/env python3
"""
Script to fix Qdrant indexes for invoice data filtering.

This script creates the necessary payload indexes for the Qdrant collection
to enable filtering by status, employee_name, and other fields.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def fix_qdrant_indexes():
    """Fix Qdrant indexes for proper filtering."""
    try:
        # Initialize Qdrant client
        client = QdrantClient(
            url=settings.QDRANT_URL, 
            api_key=settings.QDRANT_API_KEY
        )
        
        collection_name = settings.COLLECTION_NAME
        logger.info(f"Working with collection: {collection_name}")
        
        # Check if collection exists
        try:
            collection_info = client.get_collection(collection_name)
            logger.info(f"Collection exists with {collection_info.points_count} points")
        except Exception as e:
            logger.error(f"Collection does not exist: {e}")
            return False
        
        # Create indexes for filtering fields
        indexes_to_create = [
            ("status", PayloadSchemaType.KEYWORD),
            ("employee_name", PayloadSchemaType.KEYWORD),
            ("doc_type", PayloadSchemaType.KEYWORD),
            ("currency", PayloadSchemaType.KEYWORD),
            ("total_amount", PayloadSchemaType.FLOAT),
            ("reimbursement_amount", PayloadSchemaType.FLOAT),
        ]
        
        for field_name, field_type in indexes_to_create:
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                logger.info(f"✅ Created index for field: {field_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "already indexed" in str(e).lower():
                    logger.info(f"✅ Index already exists for field: {field_name}")
                else:
                    logger.warning(f"⚠️ Failed to create index for {field_name}: {e}")
        
        # Verify indexes by testing a search with filter
        logger.info("Testing search with status filter...")
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="status",
                        match=MatchValue(value="declined")
                    )
                ]
            )
            
            # Test search with filter
            results = client.search(
                collection_name=collection_name,
                query_vector=[0.0] * 384,  # Dummy vector for test
                query_filter=search_filter,
                limit=1,
                with_payload=True
            )
            
            logger.info(f"✅ Filter test successful! Found {len(results)} results with status filter")
            return True
            
        except Exception as e:
            logger.error(f"❌ Filter test failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing indexes: {e}", exc_info=True)
        return False

async def main():
    """Main function."""
    print("🔧 Fixing Qdrant indexes for invoice data filtering")
    print("=" * 60)
    
    success = await fix_qdrant_indexes()
    
    if success:
        print("✅ Successfully fixed Qdrant indexes!")
        print("The chatbot should now be able to filter invoices properly.")
    else:
        print("❌ Failed to fix indexes. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
