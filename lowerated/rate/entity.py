import json
from typing import Dict, List
from lowerated.rate.utils import get_rating


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
        "weights": {
        "Cinematography": 1,
        "Direction": 1,
        "Story": 1,
        "Characters": 1,
        "Production Design": 1,
        "Unique Concept": 1,
        "Emotions": 1
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
            return
