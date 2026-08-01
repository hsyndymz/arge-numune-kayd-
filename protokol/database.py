from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

import os

# UPDATED: Relative path logic for USB Portability
# This allows the app to run from any drive (USB, Desktop, etc)
# as long as the folder structure is preserved:
#  /Root
#    /AR-GE TAKİP VE KAYIT SİSTEMİ
#    /protokol

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sibling_name = "AR-GE TAKİP VE KAYIT SİSTEMİ"
# Go up one level (from 'protokol'), then into sibling
main_db_rel = os.path.join(BASE_DIR, "..", sibling_name, "data", "numune_takip.db")
MAIN_DB_PATH = os.path.abspath(main_db_rel)

print(f"DEBUG: Resolving DB Path: {MAIN_DB_PATH}")

if not os.path.exists(MAIN_DB_PATH):
    print("WARNING: Database file not found at resolved path!")
else:
    print("DEBUG: Database file found.")

# Fix for Windows paths/encoding in SQLAlchemy
# We use a creator function to bypass URL parsing issues with special characters
import sqlite3
def get_db_connection():
    return sqlite3.connect(MAIN_DB_PATH, check_same_thread=False)

# Use 'sqlite://' as a placeholder, the creator does the real work
# This avoids any file path parsing by SQLAlchemy itself
DATABASE_URL = "sqlite://" 

try:
    engine = create_engine(DATABASE_URL, creator=get_db_connection)
    print("DEBUG: Engine created.")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("DEBUG: SessionLocal created.")
    Base = declarative_base()
    print("DEBUG: Base defined.")
except Exception as e:
    print(f"CRITICAL INIT ERROR: {e}")

class Protocol(Base):
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, index=True)
    sequence_no = Column(Integer, nullable=True) # Sıra No
    office_record_no = Column(String, nullable=True) # Büro Kayıt No
    protocol_no = Column(String, nullable=True) # Protokol No
    region_no = Column(Integer, nullable=True) # Bölge No
    sender = Column(String, nullable=True) # NUMUNEYİ GÖNDEREN
    firm = Column(String, nullable=True) # PROTOKOL BEDELİNİ YATIRAN FİRMA
    job_description = Column(String, nullable=True) # YAPILACAK İŞ
    protocol_date = Column(String, nullable=True) # Protokol İmzalanma Tarihi
    base_cost = Column(Float, nullable=True) # Deney 1.Keşif Özeti (H)
    kdv_amount = Column(Float, nullable=True) # KDV (I)
    total_cost_with_kdv = Column(Float, nullable=True) # KDV'li 1.Keşif Özeti (J)
    turkak_fee = Column(Float, nullable=True) # TÜRKAK Payı (K)
    secondary_keşif_with_kdv = Column(Float, nullable=True) # KDV'li 2.Keşif Tutarı (i)
    stamp_tax = Column(Float, nullable=True) # Damga Vergisi
    total_amount = Column(Float, nullable=True) # Toplam Miktar
    payment_date = Column(String, nullable=True) # DEKONT Tarihi
    receipt_no = Column(String, nullable=True) # DEKONT NO:
    bank_info = Column(String, nullable=True) # AÇIKLAMA (Bank info usually here)
    month = Column(String, nullable=True) # Added for filtering
    is_archived = Column(Integer, default=0) # 0 for active, 1 for archived
    archive_year = Column(String, nullable=True) # E.g. "2025"

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
