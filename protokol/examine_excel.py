import pandas as pd
import json
import os

file_path = "2026 PROTOKOL LİSTESİ -SİBEL.xlsx"

if not os.path.exists(file_path):
    print(f"Error: File {file_path} not found.")
    exit(1)

try:
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    
    summary = {
        "file_name": file_path,
        "sheets": []
    }
    
    for sheet in sheet_names:
        # Read the sheet starting from headers
        df_data = pd.read_excel(file_path, sheet_name=sheet, skiprows=4)
        
        # Identify key columns by index if names are messy
        # Col 4: sender, Col 8: firm, Col 12: work
        # But let's use the names we found if they match
        sender_col = "NUMUNEYİ  GÖNDEREN"
        firm_col = "PROTOKOL BEDELİNİ  YATIRAN  FİRMA"
        work_col = "YAPILACAK İŞ"
        
        # Filter for rows that have at least one of these NOT NULL
        # Use columns that actually exist
        available_cols = df_data.columns.tolist()
        filter_cols = [c for c in [sender_col, firm_col, work_col] if c in available_cols]
        
        if filter_cols:
            df_meaningful = df_data.dropna(subset=filter_cols, how='all')
        else:
            # Fallback to third column if names are totally different
            df_meaningful = df_data.dropna(how='all')
            
        records = json.loads(df_meaningful.to_json(orient="records", date_format="iso", force_ascii=False))
        sheet_info = {
            "name": sheet,
            "total_meaningful_entries": len(df_meaningful),
            "sample_entries": records[:20] # Take up to 20 actual entries
        }
        summary["sheets"].append(sheet_info)
        
    with open("summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("Summary written to summary.json")
except Exception as e:
    print(f"Error reading Excel file: {e}")
