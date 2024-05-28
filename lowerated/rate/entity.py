import json
from typing import List


class Entity:
    entities = {}
    with open('./lowerated/rate/entities.json', 'r') as file:
        entities = json.load(file)

    def __init__(self, name, attributes=None):
        if name in Entity.entities:
            if attributes is None:
                self.attributes = Entity.entities[name].attributes
            else:
                self.attributes = attributes
        else:
            self.attributes = attributes
            Entity.entities[name] = self

    def __str__(self):
        return f"Entity: {self.attributes}"

    def get_attributes(self):

        return self.attributes

    def get_entities():

        return Entity.entities.keys()

    def get_entity(name):

        return Entity.entities[name]

    def get_entity_attributes(name):

        return Entity.entities[name].attributes

    def rate(reviews: List[str] = None, links: List[str] = None, file_path: str = None) -> None:

        pass
