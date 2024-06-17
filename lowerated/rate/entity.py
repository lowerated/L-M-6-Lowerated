import json
from typing import List
import pandas as pd
from lowerated.rate.utils import get_probabilities
from lowerated.rate.reviews_extraction import read_reviews
import requests


class Entity:
    entities = {}
    with open('./lowerated/rate/entities.json', 'r') as file:
        entities = json.load(file)

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
        """
        Returns attributes of the current entity.
        """
        return self.attributes

    @staticmethod
    def get_entities():
        """
        Returns all available default entities.
        """
        return Entity.entities.keys()

    @staticmethod
    def get_entity_attributes(name: str) -> List[str]:
        """
        Returns attributes of the entity mentioned in the argument
        """
        entity = Entity.entities.get(name, None)
        if entity:
            return list(entity['attributes'])
        else:
            return None

    def rate(self, reviews: List[str] = None, file_path: str = None, download_link: str = None, review_column: str = None, openai_key: str = None):
        """
        Using Reviews directly given in a list of strings, or a path to csv, xlsx, or txt file with reviews listed in one column,
        Rate the Attributes of the Entities in the Reviews, then average out one value for each attribute.

        Args:
            reviews: list of textual reviews
            review_column: helps in specifying the review column.
            range: if the reviews are too many and the cost is too much, you can test the rating on limited reviews.
            file_path: path to csv, xlsx, or txt file with reviews listed in one column. If more than one column, then each column is treated as an attribute.
            download_link: URL to download the file.
            openai_key: OpenAI API key (costs: {--} per 1000 Reviews)

        Returns:
            probabilities: Json with 7 attributes of the entity and their values.
                           Example: {
                                        "price": 0.5,
                                        "quality": 0.8,
                                        "design": 0.3,
                                        "usability": 0.6,
                                        "performance": 0.7,
                                        "features": 0.4,
                                        "support": 0.9
                           }
        """
        if reviews is None:
            reviews = read_reviews(file_path=file_path,
                                   download_link=download_link, review_column=review_column)

        if reviews:
            probabilities = get_probabilities(
                reviews=reviews, entity=self.name, attributes=self.attributes, key=openai_key)
            return probabilities
        else:
            print("No reviews to process.")
            return

    def get_reviews_insights():
        pass
