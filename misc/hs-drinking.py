import pandas as pd

# Load the CSV file
file_path = "./.data/hs-drinking-logs-feb25.csv"  # Update path if needed
df = pd.read_csv(file_path)

# Convert 'Time logged' to datetime
df['Time logged'] = pd.to_datetime(df['Time logged'], format="%d/%m/%Y %H:%M:%S")

# Extract relevant time features
df['Hour'] = df['Time logged'].dt.hour
df['Date'] = df['Time logged'].dt.date

# Calculate daily drinking frequency
daily_drinking_events = df.groupby('Date').size()

# Identify extreme drinking days (top 10%)
threshold = daily_drinking_events.quantile(0.90)
extreme_days = daily_drinking_events[daily_drinking_events >= threshold].index

# Filter data for extreme drinking days
extreme_days_data = df[df['Date'].isin(extreme_days)]

# Identify staff logging most frequently on extreme days
extreme_logged_by_pattern = extreme_days_data.groupby(['Date', 'Logged by'])['Amount 1'].sum()
extreme_staff_counts = extreme_logged_by_pattern.reset_index().groupby('Logged by')['Amount 1'].count()

# Find staff who logged multiple extreme days
frequent_loggers = extreme_staff_counts[extreme_staff_counts > 1]

# Assign shifts based on hour ranges
extreme_days_data['Shift'] = pd.cut(
    extreme_days_data['Hour'],
    bins=[0, 8, 16, 24],
    labels=['Night', 'Morning', 'Afternoon'],
    right=False
)

# Analyze drinking amounts by shift on extreme days
extreme_shift_pattern = extreme_days_data.groupby(['Date', 'Shift'])['Amount 1'].sum()

# Display results
print("Frequent Loggers on Extreme Days:\n", frequent_loggers)
print("\nDrinking Patterns by Shift on Extreme Days:\n", extreme_shift_pattern)
