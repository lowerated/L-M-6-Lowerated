from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer
import json
from typing import Dict, List
import numpy as np
from lowerated.rate.utils import predict_sentiment, compute_overall_rating, get_weights, rolling_mean_update

# Load entity weights
with open('./lowerated/rate/entities.json', 'r') as file:
    entity_data = json.load(file)

# Entity class definition
class Entity:
    entities = entity_data

    def __init__(self, name, attributes=None):
        self.name = name
        if name in Entity.entities:
            if attributes is None:
                self.attributes = Entity.entities[name]['attributes']
            else:
                self.attributes = attributes
        else:
            self.attributes = attributes
            Entity.entities[name] = {'attributes': attributes}

    def __str__(self):
        return f"Entity: {self.attributes}"

    def get_attributes(self):
        return self.attributes

    def get_weights(self):
        return Entity.entities.get(self.name, {}).get('weights', {label: 1 for label in label_columns})

    @staticmethod
    def get_entities():
        return Entity.entities.keys()

    @staticmethod
    def get_entity_attributes(name: str) -> List[str]:
        entity = Entity.entities.get(name, None)
        if entity:
            return list(entity['attributes'])
        else:
            return None

    def rate(self, reviews: List[str] = None, file_path: str = None, download_link: str = None, review_column: str = None):
        if reviews is None:
            reviews = read_reviews(file_path=file_path, download_link=download_link, review_column=review_column)

        if reviews:
            probabilities = get_rating(reviews=reviews, entity=self.name, attributes=self.attributes)
            return probabilities
        else:
            print("No reviews to process.")
            return

# Implement get_rating function
def get_rating(reviews: List[str], entity: str, attributes: List[str]) -> Dict[str, float]:
    """
    Returns the Probabilities of the Attributes in the Text

    Args:
        reviews: List of review texts
        entity: Name of the entity
        attributes: List of Attributes to rate

    Return:
        Dict: Probabilities of the Attributes {"attribute_1":0.3,"attribute_2":0.7} i.e Aspect-wise weighted mean.
        LM6: Final Rating
    """
    try:
        probabilities = {attribute: 0.0 for attribute in attributes}
        count = 0

        for review in reviews:
            sentiment_scores = predict_sentiment(review)
            for i, attribute in enumerate(attributes):
                probabilities[attribute] = rolling_mean_update(probabilities[attribute], sentiment_scores[i], count)
            count += 1

        overall_rating = compute_overall_rating(np.array([probabilities[attr] for attr in attributes]), get_weights(entity))
        probabilities['Overall Rating'] = overall_rating

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}
