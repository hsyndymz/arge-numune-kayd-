
import sys
import os

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Protocol, MAIN_DB_PATH

print(f"DEBUG: Connecting to DB at {MAIN_DB_PATH}")


import sqlite3

# Test Raw SQLite First
print(f"DEBUG: Testing Raw SQLite Connection to: {MAIN_DB_PATH}")
try:
    conn = sqlite3.connect(MAIN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM protocols")
    print(f"Raw SQLite Count: {cur.fetchone()[0]}")
    conn.close()
    print("DEBUG: Raw SQLite Success!")
except Exception as e:
    print(f"CRITICAL ERROR (Raw SQLite): {e}")

# Now ORM
print("\nDEBUG: Testing SQLAlchemy ORM...")
try:
    db = SessionLocal()
    # 1. Total Count
    total = db.query(Protocol).count()
    print(f"Total Protocols in DB: {total}")

    # 2. Archived Count
    archived = db.query(Protocol).filter(Protocol.is_archived == 1).count()
    print(f"Archived Protocols: {archived}")

    # 3. Active Count (what app shows by default)
    active_query = db.query(Protocol).filter(Protocol.is_archived == 0)
    active_count = active_query.count()
    print(f"Active Protocols (is_archived=0): {active_count}")

    # 4. List some active params
    print("\n--- First 5 Active Protocols (Ordered by Payment Date DESC) ---")
    protocols = active_query.order_by(Protocol.payment_date.desc()).limit(5).all()
    
    for p in protocols:
        print(f"ID: {p.id} | Date: {p.payment_date} | Firm: {p.firm} | Total: {p.total_amount}")

    if active_count == 0:
        print("\nWARNING: No active protocols found! Check is_archived values.")
        # Check if is_archived is maybe NULL
        null_archived = db.query(Protocol).filter(Protocol.is_archived == None).count()
        print(f"Protocols with is_archived=NULL: {null_archived}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR (ORM): {e}")
finally:
    if 'db' in locals():
        db.close()
