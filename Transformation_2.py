import pandas as pd
import re
import numpy as np

file_path = r"C:\Users\Sahanar\Downloads\Tata Harper Raw Sales\Tata Harper Raw Sales\report[5].csv"

# Step 1: Read the file, skipping the first 6 rows
df = pd.read_csv(
    file_path,
    sep=',',
    quotechar='"',
    engine='python',
    header=None,
    skiprows=6,
    encoding='ISO-8859-1',
    on_bad_lines='skip'
)

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

# Step 3: Remove columns containing 'Quantity'
df = df.loc[:, ~df.columns.str.contains('Quantity', case=False, na=False)]

# Step 4: Remove summary rows (like "Total - Tata Harper" and "Total")
first_col = df.columns[0]
df = df[~df[first_col].astype(str).str.strip().str.lower().str.startswith('total')]

# Step 5: Extract the date range from the original file (first 6 rows)
with open(file_path, encoding='ISO-8859-1') as f:
    lines = [next(f) for _ in range(6)]
date_line = next((line for line in lines if re.search(r'\d{4}', line)), "")
date_match = re.search(r'(\w+ \d{1,2}, \d{4})\s*-\s*(\w+ \d{1,2}, \d{4})', date_line)
date_range = date_match.group(0) if date_match else ""

# Step 6: Melt the DataFrame
id_vars = ['Name', 'Display Name']
value_vars = [col for col in df.columns if col not in id_vars]
df_melted = df.melt(id_vars=id_vars, value_vars=value_vars,
                    var_name='Brand_Amount', value_name='Amount (Net)')
df_melted = df_melted[df_melted['Amount (Net)'].notna() & (df_melted['Amount (Net)'].astype(str).str.strip() != '')]
df_melted['Brand'] = df_melted['Brand_Amount'].str.replace(r' Amount.*', '', regex=True)
df_melted['Date'] = date_range

# Remove rows where Brand is 'Brand', 'Tata Harper', or 'Total'
df_melted = df_melted[~df_melted['Brand'].isin(['Brand', 'Tata Harper', 'Total'])]

# Step 7: Reorder columns
df_melted = df_melted[['Name', 'Display Name', 'Brand', 'Amount (Net)', 'Date']]

# Move 'Date' column to the first position
cols = df_melted.columns.tolist()
cols.insert(0, cols.pop(cols.index('Date')))
df_melted = df_melted[cols]

# Convert 'Name' to numeric (float or int)
df_melted['Name'] = pd.to_numeric(df_melted['Name'], errors='coerce')

# Convert 'Amount (Net)' to numeric, handling $ and parentheses for negatives
def parse_amount(val):
    if pd.isnull(val) or str(val).strip() == '':
        return np.nan
    val = str(val).replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
    try:
        return float(val)
    except ValueError:
        return np.nan

df_melted['Amount (Net)'] = df_melted['Amount (Net)'].apply(parse_amount)

# If you want to display Amount (Net) with a dollar sign:
#df_melted['Amount (Net)'] = df_melted['Amount (Net)'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")

# Create dynamic filename using date range
date_str = df_melted['Date'].iloc[0].replace(' ', '_').replace(',', '').replace('-', 'to')
output_path = fr"C:\Users\Sahanar\Downloads\Report_{date_str}.xlsx"

# Step 8: Save to Excel
df_melted.to_excel(output_path, index=False)

print(f"✅ Cross table saved to: {output_path}")









