import pandas as pd
import matplotlib.pyplot as plt

# Load your data
file_path = './.data/lmcExportLogs17012025.csv'  # Replace with the correct path to your CSV file
data = pd.read_csv(file_path)

# Function to categorize descriptions into themes
def categorize_description(description):
    description = str(description).lower()
    if any(keyword in description for keyword in ['outing', 'trip', 'shopping', 'walk', 'park', 'outside']):
        return 'In the Community'
    elif any(keyword in description for keyword in ['watching tv', 'resting', 'tired', 'relaxing']):
        return 'Passive Activities'
    elif any(keyword in description for keyword in ['bingo', 'bowling', 'event', 'activity']):
        return 'Events'
    elif any(keyword in description for keyword in ['spoke', 'chatting', 'interacting', 'social']):
        return 'Social Interaction'
    elif any(keyword in description for keyword in ['declined', 'changed her mind', 'chose']):
        return 'Personal Choice'
    elif any(keyword in description for keyword in ['reading', 'writing', 'puzzle', 'games']):
        return 'Cognitive Activities'
    elif any(keyword in description for keyword in ['cleaning', 'chores', 'helping']):
        return 'Domestic Activities'
    elif any(keyword in description for keyword in ['music', 'singing', 'dancing']):
        return 'Creative Arts'
    elif any(keyword in description for keyword in ['exercise', 'gym', 'fitness']):
        return 'Physical Activities'
    elif any(keyword in description for keyword in ['meal', 'cooking', 'eating']):
        return 'Meals and Cooking'
    elif any(keyword in description for keyword in ['appointment', 'doctor', 'therapy']):
        return 'Medical Appointments'
    else:
        return 'Miscellaneous'

# Remove unwanted rows
exclusions = ['speaking space', 'way ahead', 'karibu']
data = data[~data['Description'].str.contains('|'.join(exclusions), case=False, na=False)]

# Apply the categorization to the Description column
data['Activity Theme'] = data['Description'].apply(categorize_description)

#Ensure the "Time Logged" column exists and parse it as datetime
if 'Time logged' in data.columns:
    data['Time logged'] = pd.to_datetime(data['Time logged'], errors='raise')
else:
    print("The 'Time Logged' column is missing in the dataset.")

#Sort the filtered data by "Time Logged"
data = data.sort_values(by='Time logged',ascending=False)


# Filter for "In the Community" theme (if needed)
community_data = data[data['Activity Theme'] == 'In the Community']

# Anonymize the names to initials
community_data.loc[:, 'Resident'] = community_data['Resident'].apply(
    lambda x: '.'.join([name[0].upper() for name in str(x).split()]) if isinstance(x, str) else x
)


# Count the occurrences of each theme
activity_theme_counts = data['Activity Theme'].value_counts()

# Extract main items for subtitle
main_items = {
    'In the Community': ['outing', 'trip', 'shopping', 'walk', 'park', 'outside'],
    'Passive Activities': ['watching tv', 'resting', 'tired', 'relaxing'],
    'Events': ['bingo', 'bowling', 'event', 'activity'],
    'Social Interaction': ['spoke', 'chatting', 'interacting', 'social'],
    'Personal Choice': ['declined', 'changed her mind', 'chose'],
    'Cognitive Activities': ['reading', 'writing', 'puzzle', 'games'],
    'Domestic Activities': ['cleaning', 'chores', 'helping'],
    'Creative Arts': ['music', 'singing', 'dancing'],
    'Physical Activities': ['exercise', 'gym', 'fitness'],
    'Meals and Cooking': ['meal', 'cooking', 'eating'],
    'Medical Appointments': ['appointment', 'doctor', 'therapy'],
    'Miscellaneous': ['unclear or other activities']
}

# Plotting the bar chart
plt.figure(figsize=(12, 8))
bars = plt.bar(activity_theme_counts.index, activity_theme_counts.values, color='skyblue', edgecolor='black')

# Highlight 'In the Community' bar strongly
for bar, theme in zip(bars, activity_theme_counts.index):
    if theme == 'In the Community':
        bar.set_color('orange')

# Adding annotations to display main items captured in each category
subtitle = "\n".join([f"{theme}: {', '.join(items)}" for theme, items in main_items.items()])
plt.title('Activity Breakdown by Description Themes', fontsize=16)
plt.suptitle(f"Key Items in Categories:\n{subtitle}", fontsize=10, y=0.88, color='gray', ha='left', x=0.02)
plt.xlabel('Activity Theme', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save the filtered "In the Community" data with activity themes to a new CSV file
# Keep only relevant columns: Name, Description, and any other required fields
community_data = community_data[['Time logged','Resident', 'Description', 'Logged by']]
community_output_file_path = file_path.replace('.csv', '_community_with_themes.csv')  # Adds '_community_with_themes' to the original file name
community_data.to_csv(community_output_file_path, index=False)

# Show the plot
plt.show()

# Optionally, save the chart as an image file
# plt.savefig('activity_breakdown_chart.png')
