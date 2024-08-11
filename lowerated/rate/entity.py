import json
from typing import Dict, List
from lowerated.rate.utils import get_rating, update_rating_with_new_review
from lowerated.rate.reviews_extraction import read_reviews

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
                'Cinematography': 0.14704225352112676,
                'Direction': 0.1447887323943662,
                'Story': 0.1563380281690141,
                'Characters': 0.1447887323943662,
                'Production Design': 0.12929577464788733,
                'Unique Concept': 0.13464788732394367,
                'Emotions': 0.14309859154929577
            }
        }
    }

    def __init__(self, name: str, attributes: List[str] = None):
        """
        Description:
            Initialize an Entity object with a name and optional attributes. If the entity name exists in the predefined entities,
            it uses the existing attributes; otherwise, it sets the provided attributes.

        Args:
            name (str): The name of the entity (e.g., 'Movie').
            attributes (List[str], optional): A list of attributes associated with the entity. Defaults to None.

        Return:
            None
        """
        self.name = name
        if name in Entity.entities:
            if attributes is None:
                self.attributes = Entity.entities[name]['attributes']
            else:
                self.attributes = attributes
        else:
            self.attributes = attributes
            Entity.entities[name] = {'attributes': attributes}

    def __str__(self) -> str:
        """
        Description:
            Provide a string representation of the Entity object.

        Args:
            None

        Return:
            str: A string describing the entity's attributes.
        """
        return f"Entity: {self.attributes}"

    def get_attributes(self) -> List[str]:
        """
        Description:
            Retrieve the list of attributes associated with the entity.

        Args:
            None

        Return:
            List[str]: A list of attribute names.
        """
        return self.attributes

    def get_weights(self) -> Dict[str, float]:
        """
        Description:
            Retrieve the weights for each attribute of the entity. If weights are not predefined, assigns a default weight of 1 to each attribute.

        Args:
            None

        Return:
            Dict[str, float]: A dictionary mapping attribute names to their weights.
        """
        return Entity.entities.get(self.name, {}).get('weights', {label: 1 for label in self.attributes})

    @staticmethod
    def get_entities() -> List[str]:
        """
        Description:
            Retrieve a list of all predefined entity names.

        Args:
            None

        Return:
            List[str]: A list of entity names.
        """
        return list(Entity.entities.keys())

    @staticmethod
    def get_entity_attributes(name: str) -> List[str]:
        """
        Description:
            Retrieve the attributes associated with a specific entity.

        Args:
            name (str): The name of the entity.

        Return:
            List[str]: A list of attributes for the entity. Returns None if the entity does not exist.
        """
        entity = Entity.entities.get(name, None)
        if entity:
            return list(entity['attributes'])
        else:
            return None

    def rate(self, reviews: List[str] = None, file_path: str = None, download_link: str = None, review_column: str = None) -> Dict[str, float]:
        """
        Description:
            Calculate the sentiment ratings for the entity based on provided reviews. Reviews can be directly provided as a list,
            read from a file, or downloaded from a link.

        Args:
            reviews (List[str], optional): A list of review texts. Defaults to None.
            file_path (str, optional): Path to a file containing reviews. Defaults to None.
            download_link (str, optional): URL to download reviews. Defaults to None.
            review_column (str, optional): The column name in the file or downloaded data that contains the review texts. Defaults to None.

        Return:
            Dict[str, float]: A dictionary of sentiment scores for each attribute, including the overall 'LM6' rating.
                              Returns None if no reviews are available.
        """
        if reviews is None:
            reviews = read_reviews(file_path=file_path, download_link=download_link, review_column=review_column)

        if reviews:
            rating = get_rating(reviews=reviews, entity=self.name, attributes=self.attributes, entity_data=self.entities)
            return rating
        else:
            print("No reviews to process.")
            return None

    def update_rating(self, new_review: str, current_ratings: Dict[str, float], count: int) -> Dict[str, float]:
        """
        Description:
            Update the current sentiment ratings of the entity with a new review using a rolling mean approach.

        Args:
            new_review (str): The new review text to incorporate.
            current_ratings (Dict[str, float]): The current ratings for each attribute.
            count (int): The number of reviews considered so far.

        Return:
            Dict[str, float]: The updated ratings for each attribute, including the overall 'LM6' rating.
                              Returns the current ratings if inputs are invalid.
        """
        if new_review and current_ratings and count >= 0:
            updated_ratings = update_rating_with_new_review(
                review=new_review,
                current_ratings=current_ratings,
                count=count,
                entity=self.name,
                attributes=self.attributes,
                entity_data=self.entities
            )
            return updated_ratings
        else:
            print("Invalid input for updating ratings.")
            return current_ratings
