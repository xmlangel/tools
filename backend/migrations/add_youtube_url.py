"""
Migration script to add youtube_url column to jobs table
Run this once to update the database schema
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/youtube_stt_db")

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='jobs' AND column_name='youtube_url'
        """))
        
        if result.fetchone() is None:
            # Add column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE jobs 
                ADD COLUMN youtube_url TEXT
            """))
            conn.commit()
            print("✅ Successfully added youtube_url column to jobs table")
        else:
            print("⚠️ youtube_url column already exists")

if __name__ == "__main__":
    migrate()
