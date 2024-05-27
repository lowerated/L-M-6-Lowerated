import numpy as np
import json


def entities():
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        # just the keys from data in a list
        entities = list(data.keys())
        return entities


def create_entity():
    pass
