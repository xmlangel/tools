"""
Migration script to add provider field and rename openwebui_url to api_url in llm_configs table
Run this once to update the database schema
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/youtube_stt_db")

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if provider column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='llm_configs' AND column_name='provider'
        """))
        
        if result.fetchone() is None:
            # Add provider column with default value 'openwebui'
            conn.execute(text("""
                ALTER TABLE llm_configs 
                ADD COLUMN provider VARCHAR DEFAULT 'openwebui'
            """))
            conn.commit()
            print("✅ Successfully added provider column to llm_configs table")
        else:
            print("⚠️ provider column already exists")
        
        # Check if api_url column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='llm_configs' AND column_name='api_url'
        """))
        
        if result.fetchone() is None:
            # Rename openwebui_url to api_url
            conn.execute(text("""
                ALTER TABLE llm_configs 
                RENAME COLUMN openwebui_url TO api_url
            """))
            conn.commit()
            print("✅ Successfully renamed openwebui_url to api_url in llm_configs table")
        else:
            print("⚠️ api_url column already exists (openwebui_url already renamed)")
        
        print("🎉 Migration completed successfully!")

if __name__ == "__main__":
    migrate()
