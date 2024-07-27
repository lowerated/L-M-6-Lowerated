import pandas as pd

# Load your data
df1 = pd.read_csv('../data/labeled_imdb_reviews.csv')
df2 = pd.read_csv('../data/labeled_imdb_reviews_2.csv')
df3 = pd.read_csv('../data/labeled_imdb_reviews_3.csv')
df4 = pd.read_csv('../data/labeled_imdb_reviews_4.csv')
# df5 = pd.read_csv('../data/labeled_synth_reviews_5.csv')

# merge all
df = pd.concat([df1, df2, df3, df4])

# drop duplicates
df = df.drop_duplicates(subset='review')

# drop rows with empty text
df = df.dropna(subset=['review'])

# reset index
df = df.reset_index(drop=True)

df.to_csv("../data/train_reviews.csv")

df