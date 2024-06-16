import json
from typing import List
import pandas as pd
from lowerated.rate.utils import get_probabilities
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

    def rate(self, reviews: List[str] = None, file_path: str = None, download_link: str = None, openai_key: str = None):
        """
        Using Reviews directly given in a list of strings, or a path to csv, xlsx, or txt file with reviews listed in one column,
        Rate the Attributes of the Entities in the Reviews, then average out one value for each attribute.

        Args:
            reviews: list of textual reviews
            file_path: path to csv, xlsx, or txt file with reviews listed in one column. If more than one column, then each column is treated as an attribute.
            download_link: URL to download the file
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
        if reviews is None and file_path is None and download_link is None:
            print("No Reviews Given")
            return

        if download_link:
            try:
                response = requests.get(download_link)
                response.raise_for_status()  # Check if the download was successful

                content_disposition = response.headers.get(
                    'content-disposition')
                if content_disposition:
                    filename = content_disposition.split(
                        'filename=')[-1].strip('"')
                else:
                    filename = download_link.split('/')[-1]

                if filename.endswith('.csv'):
                    df = pd.read_csv(pd.compat.StringIO(response.text))
                    reviews = df.iloc[:, 0].tolist()
                elif filename.endswith('.xlsx'):
                    df = pd.read_excel(pd.compat.BytesIO(response.content))
                    reviews = df.iloc[:, 0].tolist()
                elif filename.endswith('.txt'):
                    reviews = response.text.splitlines()
                    # Remove any extra whitespace
                    reviews = [review.strip() for review in reviews]
                else:
                    print("Unsupported file format")
                    return
            except requests.exceptions.RequestException as e:
                print(f"Failed to download the file: {e}")
                return

        elif file_path:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                reviews = df.iloc[:, 0].tolist()
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
                reviews = df.iloc[:, 0].tolist()
            elif file_path.endswith('.txt'):
                with open(file_path, 'r') as file:
                    reviews = file.readlines()
                # Remove any extra whitespace
                reviews = [review.strip() for review in reviews]
            else:
                print("Invalid File Path")
                return

        if reviews:
            probabilities = get_probabilities(
                reviews=reviews, entity=self.name, attributes=self.attributes, key=openai_key)
            return probabilities
        else:
            print("No reviews to process.")
            return

    def get_reviews_insights():
        pass
