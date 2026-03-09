import pandas as pd

# Load your CSV file
file_path = "./.data/logs_all_23012025.csv"  # Replace with your file path
df = pd.read_csv(file_path)

# Quick overview of the data
print(df.head())
print(df.info())

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Download VADER lexicon
nltk.download('vader_lexicon')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Apply sentiment analysis to the relevant text column
df['sentiment_score'] = df['Description'].apply(lambda x: sia.polarity_scores(str(x))['compound'])

# Categorize sentiment
def categorize_sentiment(score):
    if score > 0.2:
        return 'Positive'
    elif score < -0.2:
        return 'Negative'
    else:
        return 'Neutral'

df['sentiment'] = df['sentiment_score'].apply(categorize_sentiment)

# Group by staff and activity type to calculate success rate
activity_summary = df.groupby(['Logged by', 'Title', 'sentiment']).size().unstack(fill_value=0)

# Display summary
print(activity_summary)

from sklearn.feature_extraction.text import TfidfVectorizer

# Extract activity descriptions
texts = df['Description'].astype(str)

# Initialize TF-IDF Vectorizer
vectorizer = TfidfVectorizer(max_features=20, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(texts)

# Display top keywords
feature_names = vectorizer.get_feature_names_out()
keywords = tfidf_matrix.toarray().sum(axis=0)
keyword_summary = pd.DataFrame({'Keyword': feature_names, 'Importance': keywords})
print(keyword_summary.sort_values(by='Importance', ascending=False))

import matplotlib.pyplot as plt

# Plot sentiment distribution
df['sentiment'].value_counts().plot(kind='bar', color=['green', 'red', 'gray'])
plt.title("Sentiment Distribution")
plt.xlabel("Sentiment")
plt.ylabel("Count")
plt.show()

# Activity success by staff
activity_summary.plot(kind='bar', stacked=True)
plt.title("Activity Success by Staff")
plt.xlabel("Staff")
plt.ylabel("Number of Activities")
plt.show()