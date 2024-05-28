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
        """
        Returns attributes of the current entity.
        """
        return self.attributes

    def get_entities():
        """
        Returns all available default entities.
        """
        return Entity.entities.keys()
    
    def get_entity_attributes(name: str) -> List[str]:
        """
        Returns attributes of the entity mentioned in the argument
        """
        entity = Entity.entities.get(name, None)
        if entity:
            return list(entity.attributes)
        else:
            return None

    def rate(reviews: List[str] = None, file_path: str = None) -> None:
        """
        Using Reviews directly given in a list of strings, or a path to csv or xlsx file with reviews listed in one column,
        Rate the Attributes of the Entities in the Reviews, then average out one value for each attribute.

        Args:
            reviews: list of textual reviews
            file_path: path to csv or xlsx file with reviews listed in one column. If more than one column, then each column is treated as an attribute.

        Returns:
            None
        """

        if reviews is None and file_path is None:
            pass
        pass
