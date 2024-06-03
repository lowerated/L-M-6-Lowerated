import json
from typing import List
import pandas as pd
from lowerated.rate.utils import get_probabilities


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

    def rate(self, reviews: List[str] = None, file_path: str = None, download_link: str = None, openai_key: str = None) -> None:
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
            print("No Reviews Given")

        elif file_path:
            # check if file path is csv or excel
            if file_path.endswith('.csv'):
                # read csv
                df = pd.read_csv(file_path)
                reviews = df.iloc[:, 0].tolist()

            elif file_path.endswith('.xlsx'):
                # read excel
                df = pd.read_excel(file_path)
                reviews = df.iloc[:, 0].tolist()
            elif file_path.endswith('.txt'):
                # read txt file
                with open(file_path, 'r') as file:
                    reviews = file.readlines()
            else:
                print("Invalid File Path")
                return None

        elif download_link:
            # download file from link
            pass

            probabilites = get_probabilities(
                reviews=reviews, entity=self.entity, attributes=self.attributes, key=key)

        return probabilites
