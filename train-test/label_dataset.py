## Labeling Dataset

import pandas as pd
from openai import OpenAI
import csv
from dotenv import load_dotenv
import os

load_dotenv()

apikey = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=apikey)

df = pd.read_csv("../data/synth_reviews.csv")
reviews = list(df["review"])

sys_prompt = """
You are an assistant who labels movie reviews with sentiment scores for specific attributes. The attributes are Cinematography, Direction, Story, Characters, Production Design, Unique Concept, and Emotions. For each attribute, provide a sentiment score between -1 (negative) and 1 (positive). Neutral or not discussed attributes should be scored as 0. values can be in between -1 to 1 range.

YOUR INPUT WOULD BE LIKE THIS:
Review: "The cinematography was stunning, but the story was weak. I loved the movie. There wasn't anything unique in the movie. characters could've been better tho."

YOU MUST FOLLOW THE OUTPUT FORMAT GIVEN BELOW. DON'T WRITE ANYTHING ELSE:
Cinematography: 1
Direction: 0
Story: -1
Characters: -0.3
Production Design: 0
Unique Concept: -0.8
Emotions: 0

"""

# Define the attributes
attributes = ["Cinematography", "Direction", "Story", "Characters", "Production Design", "Unique Concept", "Emotions"]

def get_sentiment_scores(review):
    prompt = "Label the following review below:" + f"\nReview: {review}\n"
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt}
    ]
    )

    response = completion.choices[0].message.content.strip()
    scores = {}
    for line in response.split("\n"):
        if ":" in line:
            attr, score = line.split(":")
            scores[attr.strip()] = float(score.strip())
    return scores

def label_dataset_and_save(reviews, output_file):
    columns = ["review"] + attributes
    count = 0
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        
        for review in reviews:
            scores = get_sentiment_scores(review)
            row = [review] + [scores.get(attr, 0) for attr in attributes]
            writer.writerow(row)
            count += 1
            if count % 100 == 0:
                print(f"Processed and saved {count} reviews")

# Label the dataset and save continuously
output_file = '../data/labeled_synth_reviews_5.csv'
label_dataset_and_save(reviews, output_file)

# %%
print(f"Labeled dataset saved as {output_file}")