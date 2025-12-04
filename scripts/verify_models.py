import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.models import Entity, Instance, User, Speaker, Session, Message, KBDocument, KBChunk, KBEmbedding, SystemLog, Analytics
    print("✅ All models imported successfully.")
    
    # Print table names to verify
    print(f"Entity table: {Entity.__tablename__}")
    print(f"Instance table: {Instance.__tablename__}")
    print(f"User table: {User.__tablename__}")
    print(f"Speaker table: {Speaker.__tablename__}")
    print(f"Session table: {Session.__tablename__}")
    print(f"Message table: {Message.__tablename__}")
    print(f"KBDocument table: {KBDocument.__tablename__}")
    print(f"KBChunk table: {KBChunk.__tablename__}")
    print(f"KBEmbedding table: {KBEmbedding.__tablename__}")
    print(f"SystemLog table: {SystemLog.__tablename__}")
    print(f"Analytics table: {Analytics.__tablename__}")

except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
