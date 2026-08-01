
import os
import sys
from sqlalchemy import create_engine, text

# Add current directory to path so we can import database.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import DATABASE_URL, MAIN_DB_PATH
    print(f"Resolved DB Path: {MAIN_DB_PATH}")
    print(f"Connection String: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connection successful!")
        
        # Check table count
        result = conn.execute(text("SELECT count(*) FROM protocols"))
        count = result.scalar()
        print(f"Total Protocols: {count}")
        
        # Check last protocol
        result = conn.execute(text("SELECT id, firm, protocol_no FROM protocols ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"Latest Protocol: ID={row[0]}, Firm={row[1]}, No={row[2]}")
        else:
            print("No protocols found.")
            
except Exception as e:
    print(f"Error: {e}")
