import pandas as pd
from database import SessionLocal, Protocol, engine
import os

file_path = "2026 PROTOKOL LİSTESİ -SİBEL.xlsx"

def migrate():
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    
    db = SessionLocal()
    
    try:
        # Clear existing data to avoid duplicates if re-run
        db.query(Protocol).delete()
        db.commit()
        
        for sheet in sheet_names:
            print(f"Processing sheet: {sheet}")
            # Headers are usually at row 4 (skiprows=4)
            df = pd.read_excel(file_path, sheet_name=sheet, skiprows=4)
            
            # Key columns to check for data
            # Using column indices if names vary slightly
            # Col indices based on the analysis: 4 (Sender), 8 (Firm), 12 (Work)
            
            # We'll try to find columns by expected names first
            col_map = {
                "Sıra No": ["Sıra No:\n\n\n", "\nSıra No:\n\n\n"],
                "Büro Kayıt No": ["Büro Kayıt No:"],
                "Protokol No": ["Protokol \n No:"],
                "Bölge No": ["Bölge No"],
                "Sender": ["NUMUNEYİ  GÖNDEREN"],
                "Firm": ["PROTOKOL BEDELİNİ  YATIRAN  FİRMA"],
                "Work": ["YAPILACAK İŞ"],
                "Date": ["Protokol İmzalanma Tarihi"],
                "BaseCost": ["Deney\n1.Keşif Özeti\n(TL)"],
                "KDV": [" KDV \n ( H * %20 )\n(TL)"],
                "TotalKDV": ["KDV' li\n1.Keşif Özeti \n(TL)"],
                "Turkak": ["TÜRKAK  Payı \n( G* %06 )"],
                "StampTax": [" Damga Vergisi\n"],
                "TotalAmount": ["Toplam Miktar\n( TL )"],
                "SecondaryKeşif": ["KDV' li \n2.Keşif Tutarı \n( TL )"],
                "PaymentDate": ["DEKONT \nTarihi"],
                "ReceiptNo": ["DEKONT NO:"],
                "BankInfo": ["AÇIKLAMA"]
            }

            def get_val(row, keys):
                for k in keys:
                    if k in row:
                        val = row[k]
                        return val if pd.notna(val) else None
                return None

            for _, row in df.iterrows():
                # Filter for rows that have a firm or work description
                firm = get_val(row, col_map["Firm"])
                work = get_val(row, col_map["Work"])
                
                if firm or work:
                    # Map to model
                    p = Protocol(
                        sequence_no=get_val(row, col_map["Sıra No"]),
                        office_record_no=str(get_val(row, col_map["Büro Kayıt No"])) if get_val(row, col_map["Büro Kayıt No"]) else None,
                        protocol_no=str(get_val(row, col_map["Protokol No"])) if get_val(row, col_map["Protokol No"]) else None,
                        region_no=get_val(row, col_map["Bölge No"]),
                        sender=get_val(row, col_map["Sender"]),
                        firm=firm,
                        job_description=work,
                        protocol_date=str(get_val(row, col_map["Date"])) if get_val(row, col_map["Date"]) else None,
                        base_cost=float(get_val(row, col_map["BaseCost"])) if get_val(row, col_map["BaseCost"]) else 0.0,
                        kdv_amount=float(get_val(row, col_map["KDV"])) if get_val(row, col_map["KDV"]) else 0.0,
                        total_cost_with_kdv=float(get_val(row, col_map["TotalKDV"])) if get_val(row, col_map["TotalKDV"]) else 0.0,
                        turkak_fee=float(get_val(row, col_map["Turkak"])) if get_val(row, col_map["Turkak"]) else 0.0,
                        secondary_keşif_with_kdv=float(get_val(row, col_map["SecondaryKeşif"])) if get_val(row, col_map["SecondaryKeşif"]) else 0.0,
                        stamp_tax=float(get_val(row, col_map["StampTax"])) if get_val(row, col_map["StampTax"]) else 0.0,
                        total_amount=float(get_val(row, col_map["TotalAmount"])) if get_val(row, col_map["TotalAmount"]) else 0.0,
                        payment_date=str(get_val(row, col_map["PaymentDate"])) if get_val(row, col_map["PaymentDate"]) else None,
                        receipt_no=str(get_val(row, col_map["ReceiptNo"])) if get_val(row, col_map["ReceiptNo"]) else None,
                        bank_info=get_val(row, col_map["BankInfo"]),
                        month=sheet
                    )
                    db.add(p)
            
            db.commit()
            print(f"Finished sheet: {sheet}")

        print("Migration completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
