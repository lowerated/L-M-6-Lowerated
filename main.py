import numpy as np
from lowerated.rate.entity import Entity
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.environ["OPENAI_API_KEY"]

# Example usage
if __name__ == "__main__":
    reviews = ["Great product!", "Not worth the price.", "Excellent quality."]

    entity = Entity(name="Movie")
    attributes = entity.get_attributes()

    rating = entity.rate(
        reviews=reviews, openai_key=openai_key)

    print(rating)
