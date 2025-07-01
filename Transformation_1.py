import pandas as pd
from datetime import datetime, timedelta
import re

def get_week_end_date(fiscal_code):
    fiscal_year = int(str(fiscal_code)[:4])
    week_num = int(str(fiscal_code)[4:])
    fiscal_week1_start = datetime(fiscal_year, 4, 1)
    week_start = fiscal_week1_start + timedelta(weeks=week_num - 1)
    week_end = week_start + timedelta(days=6)
    return week_end.strftime('%Y-%m-%d')

# File path
file_path = r"C:\Users\Sahanar\Downloads\Store-Sales_1000000152_MILK MAKEUP LLC-2025-05-11.xlsx"

# Detect header row
df_preview = pd.read_excel(file_path, sheet_name=0, header=None, nrows=15)
header_row_idx = None
for idx, row in df_preview.iterrows():
    if 'Store Number' in row.values:
        header_row_idx = idx
        break
if header_row_idx is None:
    raise ValueError("❌ Couldn't locate header row with 'Store Number'")

# Load data
df = pd.read_excel(file_path, header=header_row_idx)
df.columns = df.columns.str.strip()

# 🔍 Extract all fiscal week codes from first 30 rows
sheet_raw = pd.read_excel(file_path, header=None, nrows=30)
week_codes = []
for row in sheet_raw.itertuples(index=False):
    for cell in row:
        if isinstance(cell, str) and "fiscal week" in cell.lower():
            matches = re.findall(r'20\d{4}', cell)
            for code in matches:
                if len(code) == 6:
                    week_codes.append(code)

if not week_codes:
    raise ValueError("❌ No fiscal week codes found")

# ✅ Use the highest FW number found
latest_fw_code = max(week_codes)
latest_fw = int(latest_fw_code[4:])  # Extract FW number

# Identify latest TY column
sales_ty_cols = [col for col in df.columns if 'Total Net Sales TY' in str(col)]
if not sales_ty_cols:
    raise ValueError("❌ No 'Total Net Sales TY' column found")
latest_sales_ty = sales_ty_cols[-1]

# Match LY % column
change_cols = [col for col in df.columns if 'Sales Change to LY %' in str(col)]
if not change_cols:
    raise ValueError("❌ No 'Sales Change to LY %' column found")
latest_sales_change = change_cols[-1]

# Compute LY
df['Total Sales LY'] = df[latest_sales_ty] / (1 + df[latest_sales_change])

# Get end date from latest FW code
week_end = get_week_end_date(latest_fw_code)

# Final DataFrame
df_final = df[['Store Number', 'Store Name', latest_sales_ty, latest_sales_change, 'Total Sales LY']].copy()
df_final.columns = ['Store Number', 'Store Name', 'Total Net Sales TY', 'Sales Change to LY %', 'Total Sales LY']
df_final.insert(0, 'Fiscal Week End Date', week_end)

# Save
output_path = fr"C:\Users\Sahanar\Downloads\Store_Sales_Latest_FW_{week_end}.xlsx"
df_final.to_excel(output_path, index=False)
print(f"✅ Latest FW (Week {latest_fw}) saved to: {output_path}")
