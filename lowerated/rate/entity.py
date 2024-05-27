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

    def rate(reviews: List[str]):
        pass
