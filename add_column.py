
from sqlalchemy import create_engine, text
import os

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/youtube_stt_db")

# Override purely for local test if needed, but assuming env is correct or default works.
# Wait, the user said "PostgreSQL 16. Port 5436 (host) -> 5432 (container)".
# If I run this script on HOST, I need to use port 5436.
# If I run this inside container, I use 5432.
# "Operating System: mac". I am running on host.
# So I should change port to 5436.

DATABASE_URL_HOST = "postgresql://user:password@localhost:5436/youtube_stt_db"

def upgrade_db():
    engine = create_engine(DATABASE_URL_HOST)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='llm_configs' AND column_name='is_default'"))
            if result.fetchone():
                print("Column 'is_default' already exists.")
            else:
                print("Adding column 'is_default'...")
                conn.execute(text("ALTER TABLE llm_configs ADD COLUMN is_default BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    upgrade_db()
