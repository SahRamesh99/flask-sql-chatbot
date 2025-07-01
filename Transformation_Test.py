import pandas as pd
import re

file_path = r"C:\Users\Sahanar\Downloads\Tata Harper Raw Sales\Tata Harper Raw Sales\report[5].csv"  # Change to your CSV file path

# Step 1: Read the file, skipping the first 6 rows (adjust if needed)
df = pd.read_csv(file_path, header=None, skiprows=6, encoding='ISO-8859-1')

# Step 2: Combine the first two rows for headers
header1 = df.iloc[0].fillna('').astype(str).str.strip().tolist()
header2 = df.iloc[1].fillna('').astype(str).str.strip().tolist()
filled_header1 = []
prev = ""
for cell in header1:
    if cell and cell.lower() != "nan":
        prev = cell
    filled_header1.append(prev)
combined_headers = []
for h1, h2 in zip(filled_header1, header2):
    if h2 and h2.lower() != "nan":
        combined_headers.append(f"{h1} {h2}".strip())
    else:
        combined_headers.append(h1)
df.columns = combined_headers
df = df.drop(index=[0, 1]).reset_index(drop=True)

# Step 3: Remove summary rows (like "Total - Tata Harper" and "Total")
first_col = df.columns[0]
df = df[~df[first_col].astype(str).str.strip().str.lower().str.startswith('total')]

# Step 4: Extract the date range from the original file (first 6 rows)
with open(file_path, encoding='ISO-8859-1') as f:
    lines = [next(f) for _ in range(6)]
date_line = next((line for line in lines if re.search(r'\d{4}', line)), "")
date_match = re.search(r'(\w+ \d{1,2}, \d{4})\s*-\s*(\w+ \d{1,2}, \d{4})', date_line)
date_range = date_match.group(0) if date_match else ""

# Step 5: Melt the DataFrame to long format for all stores' Amount (Net)
id_vars = ['Name', 'Display Name']
amount_cols = [col for col in df.columns if 'Amount (Net)' in col]
df_melted = df.melt(id_vars=id_vars, value_vars=amount_cols,
                    var_name='Brand', value_name='Amount (Net)')

# Step 6: Clean up the Brand column to just the store name
df_melted['Brand'] = df_melted['Brand'].str.replace(' Amount (Net)', '', regex=False)

# Step 7: Add the date column
df_melted['Date'] = date_range

# Step 8: Remove rows with missing amounts
df_melted = df_melted[
    df_melted['Amount (Net)'].notna() &
    (df_melted['Amount (Net)'].astype(str).str.strip() != '')
]

# Step 8.1: Reorder columns so Date is first
df_melted = df_melted[['Date', 'Name', 'Display Name', 'Brand', 'Amount (Net)']]

# Step 9: Save to Excel
df_melted.to_excel('pivot_to_long_sales_no_summary.xlsx', index=False)
print("✅ Saved as pivot_to_long_sales_no_summary.xlsx")