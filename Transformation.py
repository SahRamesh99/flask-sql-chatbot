import os
import pandas as pd
import re
from datetime import datetime

# === CONFIGURATION ===
base_dir = r"C:\Users\Sahanar\Downloads\Sales that need Edits (2)\Sales that need Edits"
output_dir = os.path.join(base_dir, "Processed_Outputs")
os.makedirs(output_dir, exist_ok=True)

date_regex = r"Week end date:\s*([A-Za-z]+\s\d{1,2},\s\d{4})"
batch_size = 50
max_rows_to_scan = 500
desired_fields = ['Brand', 'SKU', 'SKU Description', 'B&M SALES $', 'TTL SALES $']

# === WALK THROUGH FILES ===
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".xlsx") and not file.startswith('~$'):  # Skip temp files
            file_path = os.path.join(root, file)
            print(f"\n🔍 Processing file: {file_path}")
            try:
                xls = pd.ExcelFile(file_path)
            except Exception as e:
                print(f"❌ Failed to open {file_path}: {e}")
                continue

            summary_dfs = {}
            final_week_end_date = "Unknown"

            for sheet_name in xls.sheet_names:
                print(f"   📄 Sheet: {sheet_name}")
                # --- Step 1: Extract date ---
                week_end_date = "Unknown"
                for start_row in range(0, max_rows_to_scan, batch_size):
                    df_chunk = pd.read_excel(xls, sheet_name=sheet_name, skiprows=start_row, nrows=batch_size, header=None)
                    if df_chunk.empty:
                        break
                    found = False
                    for row in df_chunk.itertuples(index=False):
                        for cell in row:
                            if isinstance(cell, str):
                                match = re.search(date_regex, cell)
                                if match:
                                    raw_date = match.group(1).strip()
                                    try:
                                        parsed_date = datetime.strptime(raw_date, "%B %d, %Y")
                                        week_end_date = parsed_date.strftime("%Y-%m-%d")
                                    except ValueError as ve:
                                        print(f"⚠️ Failed to parse date: {ve}")
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        break

                if final_week_end_date == "Unknown" and week_end_date != "Unknown":
                    final_week_end_date = week_end_date

                # --- Step 2: Clean data ---
                try:
                    df_raw = pd.read_excel(xls, sheet_name=sheet_name, skiprows=6)
                    header_row_index = df_raw[df_raw.iloc[:, 0].astype(str).str.contains("Dept|Brand", na=False)].index[0]
                    df_raw.columns = df_raw.iloc[header_row_index]
                    df_clean = df_raw.drop(index=list(range(header_row_index + 1))).reset_index(drop=True)
                except Exception as e:
                    print(f"⚠️ Skipping sheet {sheet_name}: {e}")
                    continue

                # --- Step 3: Column mapping ---
                column_mapping = {}
                for desired in desired_fields:
                    match = next((col for col in df_clean.columns if desired.lower() in str(col).lower()), None)
                    if match:
                        column_mapping[desired] = match
                    else:
                        print(f"⚠️ Column '{desired}' not found in {sheet_name}")

                # --- Step 4: Store cleaned sheet ---
                if len(column_mapping) == len(desired_fields):
                    df_filtered = df_clean[[column_mapping[f] for f in desired_fields]].copy()
                    df_filtered.insert(0, 'Week End Date', week_end_date)
                    summary_dfs[sheet_name[:31]] = df_filtered

            # === Save individual output ===
            if summary_dfs:
                name_part = os.path.splitext(file)[0][:20]  # Base name of input file
                output_filename = f"{name_part}_{final_week_end_date}.xlsx"
                output_path = os.path.join(output_dir, output_filename)

                if os.path.exists(output_path):
                    os.remove(output_path)

                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for sheet, df in summary_dfs.items():
                        df.to_excel(writer, sheet_name=sheet[:31], index=False)

                print(f"✅ Saved processed file to: {output_path}")
