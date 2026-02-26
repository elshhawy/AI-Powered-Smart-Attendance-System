# scripts/test_connection.py
import sys
import os

# This line makes Python find the src/ package
# regardless of where you run the file from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.fetchone())