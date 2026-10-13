
from sqlalchemy import text
from backend.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("KET NOI SUPABASE THANH CONG!")
        print(result.scalar())
except Exception as e:
    print("KET NOI THAT BAI:")
    print(type(e).__name__, str(e))
