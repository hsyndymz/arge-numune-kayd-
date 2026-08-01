
import sys
import os
import traceback

# Redirect output to file
log_file = open("debug_log_full.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

print("Starting Debug View 2...")

try:
    # Ensure import path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    print(f"Added to path: {current_dir}")

    import database
    print("Imported database successfully.")
    
    from database import SessionLocal, Protocol, MAIN_DB_PATH
    
    print(f"MAIN_DB_PATH: {MAIN_DB_PATH}")
    
    # Test ORM
    db = SessionLocal()
    print("Session created.")
    
    count = db.query(Protocol).count()
    print(f"Protocol Count: {count}")
    
except Exception:
    traceback.print_exc()
finally:
    print("Finished.")
    log_file.close()
