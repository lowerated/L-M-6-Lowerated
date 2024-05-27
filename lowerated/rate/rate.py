import numpy as np
import json
from typing import List
from lowerated.rate.entity import Entity


def entities() -> List[str]:
    """
    Returns All the Default Entities Available in the Lowerated Library
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
    """
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        attributes = data[entity]
        return attributes
