import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.knowledge import KBDocument, KBChunk, KBEmbedding

async def verify_embeddings():
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        print("🚀 Verifying Embeddings...")
        
        # Count documents
        result = await session.execute(select(func.count(KBDocument.doc_id)))
        doc_count = result.scalar()
        print(f"📄 Total Documents: {doc_count}")

        # Count chunks
        result = await session.execute(select(func.count(KBChunk.chunk_id)))
        chunk_count = result.scalar()
        print(f"🧩 Total Chunks: {chunk_count}")

        # Count embeddings
        result = await session.execute(select(func.count(KBEmbedding.chunk_id)))
        embedding_count = result.scalar()
        print(f"🧠 Total Embeddings: {embedding_count}")

        if chunk_count > 0 and chunk_count == embedding_count:
            print("✅ Success: All chunks have embeddings!")
        elif chunk_count > 0:
            print(f"⚠️ Warning: {chunk_count - embedding_count} chunks are missing embeddings.")
        else:
            print("ℹ️ No chunks found.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_embeddings())
