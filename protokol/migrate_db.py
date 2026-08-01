import sqlite3
from database import Protocol
import os

def migrate():
    db_path = 'protocols.db'
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('PRAGMA table_info(protocols)')
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    model_cols = Protocol.__table__.columns.keys()
    missing = [c for c in model_cols if c not in existing_cols]
    
    if not missing:
        print("No missing columns.")
        conn.close()
        return

    print(f"Adding missing columns: {missing}")
    
    for c in missing:
        col_obj = Protocol.__table__.columns[c]
        # Determine type
        t = str(col_obj.type).upper()
        if 'INTEGER' in t:
            type_str = 'INTEGER'
        elif 'FLOAT' in t or 'DECIMAL' in t:
            type_str = 'FLOAT'
        else:
            type_str = 'TEXT'
            
        try:
            cursor.execute(f'ALTER TABLE protocols ADD COLUMN {c} {type_str}')
            print(f"Successfully added column: {c}")
        except sqlite3.OperationalError as e:
            print(f"Error adding {c}: {e}")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
