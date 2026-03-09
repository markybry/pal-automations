
import pandas as pd

# Load the CSV file (update path if needed)
df = pd.read_csv(r"./.data/brushing-logs.csv")

# Convert "Time logged" column to datetime to extract dates
df['Time logged'] = pd.to_datetime(df['Time logged'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

# Make sure 'Description' column is string type
df['Description'] = df['Description'].astype(str)

# Filter rows mentioning electric toothbrush AND not charged (or similar)
not_charged_entries = df[
    df['Description'].str.contains('electric', case=False, na=False) &
    df['Description'].str.contains('not charged|uncharged|no charge', case=False, na=False)
]

# Extract date only
not_charged_entries['Date'] = not_charged_entries['Time logged'].dt.date

# Count how many times
count_not_charged = len(not_charged_entries)

print(f"Electric toothbrush reported as not charged {count_not_charged} times.\n")

# Show date and description examples
print("Dates and descriptions when electric toothbrush was not charged:\n")
for idx, row in not_charged_entries[['Date', 'Description']].drop_duplicates().iterrows():
    print(f"- Date: {row['Date']} | Description: {row['Description']}\n")
