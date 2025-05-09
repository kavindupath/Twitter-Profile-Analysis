# -*- coding: utf-8 -*-
"""Big data Analytics- Clustering-Kavindu's Experiment.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1HORrJ_cy1929-Uh4u1NheuVextPQTDCJ

# Importing libraries and dataset
"""

# Importing libraries
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import seaborn as sns
import matplotlib.pyplot as plt
!pip install kneed
from kneed import KneeLocator
import nltk
import re
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load Twitter user data and create a copy of the DataFrame
file_path = '/content/sample_data/twitter_user_data.csv'
df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False)
df_copy = df.copy()

"""# Data Preprocessing"""

# Display DataFrame information (data types, non-null counts) and summary statistics
df.info()
df.describe()

# Compute the Correlation Matrix
columns_of_interest = ['gender:confidence', 'profile_yn:confidence', 'tweet_count', 'retweet_count', 'fav_number']
correlation_matrix = df_copy[columns_of_interest].corr()

# Visualize the Correlation Matrix
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix Heatmap')
plt.show()

#Find Highly Correlated Features (above 0.8 or below -0.8)
threshold = 0.8
highly_correlated = []

# Iterate through the correlation matrix to find feature pairs with high correlation
for i in range(len(correlation_matrix.columns)):
    for j in range(i):
        if abs(correlation_matrix.iloc[i, j]) > threshold:
            highly_correlated.append((correlation_matrix.columns[i], correlation_matrix.columns[j], correlation_matrix.iloc[i, j]))

# Display the highly correlated features
print("Highly correlated features:")
for feature1, feature2, corr_value in highly_correlated:
    print(f"{feature1} and {feature2}: {corr_value:.2f}")

# Drop unnecessary columns from the DataFrame to focus on relevant features for analysis
df.drop(['profile_yn','profile_yn:confidence','gender','gender:confidence','_unit_id','_last_judgment_at','created','profileimage','tweet_coord',
         '_trusted_judgments','tweet_created', 'tweet_id', 'tweet_location', 'user_timezone',
         '_golden','_unit_state', 'gender_gold', 'link_color', 'name', 'profile_yn_gold', 'sidebar_color'
         ], axis=1, inplace=True)
df.head(5)

# Count the number of missing (NaN) values in each column of the DataFrame
df.isna().sum()

# Replace missing values in the 'description' and 'text' columns with empty strings
df['description'].fillna('', inplace=True)
df['text'].fillna('', inplace=True)

# Clean text by removing non-alphabetic characters and converting to lowercase , and store the cleaned text in new columns

def clean(review):
    descrip = re.sub('[^a-zA-Z]', ' ', review)
    review = review.lower()
    return review

df['descrip_Cleaned'] = pd.DataFrame(df['description'].apply(lambda x: clean(x)))
df['text_Cleaned'] = pd.DataFrame(df['text'].apply(lambda x: clean(x)))
df.head()

# Remove special characters (e.g., '@', '+', '(', ')', '#') from 'descrip_Cleaned' and 'text_Cleaned' columns
# Remove URLs from both columns using regex
df['descrip_Cleaned'].replace('[@+]', "", regex=True,inplace=True)
df['descrip_Cleaned'].replace('[()]', "", regex=True,inplace=True)
df['descrip_Cleaned'].replace('[#+]', "", regex=True)

url_regex = r"(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9%._-]*)*"
df['descrip_Cleaned'] = df['descrip_Cleaned'].replace(url_regex, "", regex=True)


df['text_Cleaned'].replace('[@+]', "", regex=True,inplace=True)
df['text_Cleaned'].replace('[()]', "", regex=True,inplace=True)
df['text_Cleaned'].replace('[#+]', "", regex=True)

url_regex = r"(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9%._-]*)*"
df['text_Cleaned'] = df['text_Cleaned'].replace(url_regex, "", regex=True)

# Tokenize and clean the 'descrip_Cleaned' column
df['descrip_Cleaned'] = [nltk.word_tokenize(tweet) for tweet in df['descrip_Cleaned']]
descrip_new = [ [word for word in tweet if word.isalpha()] for tweet in df['descrip_Cleaned']]

# Remove stopwords from 'descrip_Cleaned'
stop_words = set(stopwords.words('english'))
descrip_new_alpha = [ [word for word in tweet if word not in stop_words] for tweet in descrip_new]

# Tokenize and clean the 'text_Cleaned' column
df['text_Cleaned'] = [nltk.word_tokenize(tweet) for tweet in df['text_Cleaned']]
text_new = [ [word for word in tweet if word.isalpha()] for tweet in df['text_Cleaned']]

# Remove stopwords from 'text_Cleaned'
text_new_alpha = [ [word for word in tweet if word not in stop_words] for tweet in text_new]

# Lemmatize words in the 'descrip_Cleaned' column to reduce them to their base form
description_new_lemma = []
lemma = nltk.WordNetLemmatizer()
for each_row in descrip_new_alpha:
    description_new_lemma.append([lemma.lemmatize(word) for word in each_row])
df['descrip_Cleaned'] = [" ".join(desc) for desc in description_new_lemma]

# Lemmatize words in the 'text_Cleaned' column
text_new_lemma = []
lemma2 = nltk.WordNetLemmatizer()
for each_row in text_new_alpha:
    text_new_lemma.append([lemma2.lemmatize(word) for word in each_row])
df['text_Cleaned'] = [" ".join(desc) for desc in text_new_lemma]

# scaling
df['tweet_count'] = np.log1p(df['tweet_count'])
df['retweet_count'] = np.log1p(df['retweet_count'])
df['fav_number'] = np.log1p(df['fav_number'])

df.head(3)

# Extract features from 'descrip_Cleaned' using TF-IDF with a maximum of 100 features
tfidf_vectorizer = TfidfVectorizer(max_features=100)
x = tfidf_vectorizer.fit_transform(df['descrip_Cleaned']).toarray()

# Extract features from 'text_Cleaned' using TF-IDF with the same setup
tfidf_vectorizer = TfidfVectorizer(max_features=100)
y = tfidf_vectorizer.fit_transform(df['text_Cleaned']).toarray()

# Drop the original 'description' and 'text' columns from the DataFrame as they are no longer needed
df.drop(['description', 'text'], axis=1, inplace=True)

# Display the first 3 rows of the updated DataFrame
df.head(3)

# Convert the TF-IDF feature arrays into DataFrames
A = pd.DataFrame(x)
B = pd.DataFrame(y)

# Concatenate the original DataFrame with the TF-IDF feature DataFrames
X = pd.concat([df, A, B], join='outer', axis=1)

# Display the shape of the final DataFrame
X.shape

# Drop the 'descrip_Cleaned' and 'text_Cleaned' columns as they are no longer needed
X.drop(['descrip_Cleaned'], axis=1, inplace=True)
X.drop(['text_Cleaned'], axis=1, inplace=True)

# Display information about the updated DataFrame
X.info()

# Rename columns to ensure they have string names
X = X.rename(str, axis="columns")

# Check for any remaining missing values in the DataFrame
X.isna().sum()

# Remove rows with missing values
X.dropna(inplace=True)

# Display the first 5 rows of the cleaned DataFrame
X.head(5)

"""# K-Means Clustering"""

# Finding the Optimal Number of Clusters using the Elbow Method

# Calculate Within-Cluster Sum of Squares (WCSS) for different numbers of clusters
wcss = []
max_clusters = 10  # Define the maximum number of clusters to test

for i in range(1, max_clusters + 1):
    kmeans = KMeans(n_clusters=i, random_state=42)
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)

# Plotting the Elbow Method Graph
plt.figure(figsize=(8, 6))
plt.plot(range(1, max_clusters + 1), wcss, marker='o', linestyle='-')  # Plot WCSS against the number of clusters
plt.title('Elbow Method to Determine Optimal Number of Clusters')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Within-Cluster Sum of Squares (WCSS)')
plt.xticks(range(1, max_clusters + 1))
plt.grid(True)
plt.show()

# Using kneed to find the optimal number of clusters
kneedle = KneeLocator(range(1, max_clusters + 1), wcss, curve='convex', direction='decreasing')

# Get the optimal number of clusters
optimal_k = kneedle.elbow
print(f'The optimal number of clusters is: {optimal_k}')

# Initialize and fit the KMeans clustering model with the optimal number of clusters
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
kmeans_labels = kmeans.fit_predict(X)

"""# Evaluation"""

# Evaluation
kmeans_silhouette = silhouette_score(X, kmeans_labels)
print(f'K-Means Silhouette Score: {kmeans_silhouette}')

#Visualizing Clusters with PCA and t-SNE

# PCA for Dimensionality Reduction
pca = PCA(n_components=2)
reduced_features_pca = pca.fit_transform(X)

# t-SNE for Dimensionality Reduction
tsne = TSNE(n_components=2, perplexity=30, n_iter=300, random_state=42)
reduced_features_tsne = tsne.fit_transform(X)

# Visualization using PCA
plt.figure(figsize=(8, 6))
plt.scatter(reduced_features_pca[:, 0], reduced_features_pca[:, 1], c=kmeans_labels, cmap='viridis', s=50, alpha=0.7)
plt.title('K-Means Clustering Visualization with PCA')
plt.xlabel('PCA Component 1')
plt.ylabel('PCA Component 2')
plt.colorbar(label='Cluster')
plt.show()

# Visualization using t-SNE
plt.figure(figsize=(8, 6))
plt.scatter(reduced_features_tsne[:, 0], reduced_features_tsne[:, 1], c=kmeans_labels, cmap='viridis', s=50, alpha=0.7)
plt.title('K-Means Clustering Visualization with t-SNE')
plt.xlabel('t-SNE Component 1')
plt.ylabel('t-SNE Component 2')
plt.colorbar(label='Cluster')
plt.show()



#Add cluster labels to the DataFrame
X['Cluster'] = kmeans_labels

#Summary Statistics for Each Cluster
cluster_summary = X.groupby('Cluster').describe().T
print(cluster_summary)

#Plotting countplot of clusters
pl = sns.countplot(x=X["Cluster"], palette= "flare")
pl.set_title("Distribution Of The Clusters")
plt.show()

# Visualize the distribution of genders within each cluster using a count plot
pl = sns.countplot(x=X["Cluster"], hue=df_copy["gender"], palette="mako")
pl.set_title("Gender Distribution Within Each Cluster")
plt.show()

