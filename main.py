from lowerated.rate.entity import Entity
from lowerated.rate.utils import calculate_cost
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.environ["OPENAI_API_KEY"]

# Example usage
if __name__ == "__main__":
    reviews = [
        "bad movie!", "worse than other movies.", "bad.",
        "best movie", "very good movie", "the cinematography was insane",
        "story was so beautiful", "the emotional element was missing but cinematography was great",
        "didn't feel a thing watching this",
        "oooof, eliot and jessie were so good. the casting was the best",
        "yo who designed the set, that was really good",
        "such stories are rare to find"
    ]

    # get costs
    costs = calculate_cost(reviews=reviews)
    print(f"To rate the reviews, the algorithm will cost: {costs} $")

    entity = Entity(name="Movie")
    attributes = entity.get_attributes()

    rating = entity.rate(
        reviews=reviews, openai_key=openai_key)

    print(rating)
