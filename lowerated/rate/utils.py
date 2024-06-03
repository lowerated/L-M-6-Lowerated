import numpy as np
import json
from typing import List, Dict
from lowerated.rate.entity import Entity


def entities() -> List[str]:
    """
    Returns All the Default Entities Available in the Lowerated Library

    Return:
        List[str]: List of Entities
    """
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        # just the keys from data in a list
        entities = list(data.keys())
        return entities


def find_attributes(entity: str) -> List[str]:
    """
    Returns All the Default Attributes Available in the Lowerated Library

    Args:
        entity (str): Entity Name
    Return:
        List[str]: List of Attributes
    """
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        attributes = data.get(entity, None)
        return attributes


def get_probabilities(reviews: List[str], entity: str, attributes: List[str], key: str = None) -> Dict:
    """
    Returns the Probabilities of the Attributes in the Text

    Args:
        text: A single review text
        attributes: List of Attributes to rate

    Return:
        Dict: Probabilities of the Attributes {"attribute_1":0.3,"attribute_2":0.7}
    """

    if key is None:
        return None
