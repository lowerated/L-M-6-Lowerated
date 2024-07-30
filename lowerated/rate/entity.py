import json
from typing import Dict, List
from lowerated.rate.utils import get_rating
from lowerated.rate.reviews_extraction import read_reviews
# Entity class definition
class Entity:
    entities = {
        "Movie": {
            "attributes": [
                "Cinematography",
                "Direction",
                "Story",
                "Characters",
                "Production Design",
                "Unique Concept",
                "Emotions"
            ],
            "weights":{'Cinematography': 0.14704225352112676,
                        'Direction': 0.1447887323943662, 
                        'Story': 0.1563380281690141, 
                        'Characters': 0.1447887323943662, 
                        'Production Design': 0.12929577464788733, 
                        'Unique Concept': 0.13464788732394367, 
                        'Emotions': 0.14309859154929577
            }
        }
    }

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
        return Entity.entities.get(self.name, {}).get('weights', {label: 1 for label in self.attributes})

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
            rating = get_rating(reviews=reviews, entity=self.name, attributes=self.attributes, entity_data=self.entities)
            return rating
        else:
            print("No reviews to process.")
            return None

    @staticmethod
    def scale_rating(rating: Dict[str, float]) -> Dict[str, float]:
        """
        Scale the ratings from the range -1 to 1 to the range 0 to 10.
        """
        scaled_rating = {}
        for key, value in rating.items():
            # Normalize the rating from -1 to 1 to the range 0 to 1
            normalized_value = (value + 1) / 2
            # Scale the normalized rating to the range 0 to 10
            scaled_rating[key] = normalized_value * 10
        return scaled_rating

