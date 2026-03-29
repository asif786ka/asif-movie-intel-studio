import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.scripts.seed_data import seed_sample_documents
from app.db.vector_store import vector_store


async def main():
    print("Ingesting sample documents...")
    print(f"Current chunk count: {vector_store.count()}")

    vector_store.delete_collection()
    print("Cleared existing collection")

    await seed_sample_documents()
    print(f"Final chunk count: {vector_store.count()}")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
