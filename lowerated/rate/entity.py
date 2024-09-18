import json
from typing import Dict, List, Optional, Any
from lowerated.rate.utils import (
    get_rating, update_rating_with_new_review)
from lowerated.rate.reviews_extraction import (
    get_imdb_ratings as imdb_ratings,
    get_rotten_tomatoes_ratings as rotten_tomatoes_ratings,
    get_imdb_reviews as imdb_reviews,
    get_audience_reviews_rotten_tomatoes as audience_reviews_rotten_tomatoes,
    get_critics_reviews_rotten_tomatoes as critics_reviews_rotten_tomatoes
)
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
    

    def get_imdb_rating(self,name: Optional[str] = None, urls: Optional[List[str]] = None, driver_path: Optional[str] = None):
        """
        Description:
            Scrapes IMDb ratings for specified movies either by using IMDb search results or by scraping directly from the provided IMDb movie URLs.

        Args:
            movie_name: Optional[str] - The name of the movie to search for on IMDb (only if URLs are not provided).
            movie_urls: Optional[list] - List of IMDb movie URLs to scrape ratings from directly.
            driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.

        Returns:
            list - A list of dictionaries containing the movie titles and their IMDb ratings (out of 10). If no match is found, "Not Found" is returned for the movie.
        """
        return imdb_ratings(name=name, urls=urls, driver_path=driver_path)
    

    def get_rotten_tomatoes_ratings(self, urls: Optional[List[str]] = None, name: Optional[str] = None, config: Optional[Dict[str, Dict[str, Any]]] = None, driver_path: Optional[str] = None):
        """
        Description:
            Scrapes movie ratings from Rotten Tomatoes based on provided URLs or by searching for a movie name.

        Args:
            urls: Optional[List[str]] - List of URLs to scrape ratings from.
            name: Optional[str] - Movie name to search and scrape ratings for.
            config: Optional[Dict[str, Dict[str, Any]]] - Optional configuration for scraping elements.
            driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.

        Returns:
            List[Dict[str, Any]] - A list of dictionaries containing the movie title, critics score (out of 10), and audience score (out of 10).
        """
        return rotten_tomatoes_ratings(urls=urls, name=name, config=config, driver_path=driver_path)


    def get_audience_reviews_rotten_tomatoes(self, urls: Optional[List[str]] = None, name: Optional[str] = None, driver_path: Optional[str] = None, limit: Optional[int] = None):
        """
        Description:
            Scrapes audience reviews from Rotten Tomatoes based on provided URLs or by searching for a movie name.

        Args:
            urls: Optional[List[str]] - List of URLs to scrape reviews from.
            name: Optional[str] - Movie name to search and scrape reviews for.
            driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.
            review_limit: Optional[int] - Maximum number of reviews to scrape. If None, all available reviews will be collected.

        Returns:
            List[Dict[str, Any]] - A list of dictionaries containing the movie title and a list of audience reviews.
        """
        return audience_reviews_rotten_tomatoes(urls=urls, name=name, driver_path=driver_path, limit=limit)

    def get_critics_reviews_rotten_tomatoes(self, urls: Optional[List[str]] = None, name: Optional[str] = None, driver_path: Optional[str] = None, limit: Optional[int] = None):
        """
        Description:
            Scrapes critic reviews from Rotten Tomatoes based on provided URLs or by searching for a movie name.

        Args:
            urls: Optional[List[str]] - List of URLs to scrape reviews from.
            name: Optional[str] - Movie name to search and scrape reviews for.
            driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.
            review_limit: Optional[int] - Maximum number of reviews to scrape. If None, all available reviews will be collected.

        Returns:
            List[Dict[str, Any]] - A list of dictionaries containing the movie title and a list of critic reviews.
        """
        return critics_reviews_rotten_tomatoes(urls=urls, name=name, driver_path=driver_path, limit=limit)

    def get_imdb_reviews(self,name: Optional[str] = None, urls: Optional[List[str]] = None, driver_path: Optional[str] = None, limit: int = 10):
        """
        Description:
            Scrape IMDb user reviews by searching for the movie by providing its name or a list of URLS.

        Args:
            name: str - The name of the movie to search for on IMDb. Ignored if imdb_urls are provided.
            urls: list - A list of IMDb URLs to the movie's reviews page. Overrides movie_name if provided.
            driver_path: str - Path to the ChromeDriver executable. If None, the system's default driver will be used.
            num_reviews: int - The number of reviews to scrape from each URL or search result. Default is 10.

        Returns:
            list - A list of dictionaries containing the movie titles and their IMDb user reviews.
        """
        return imdb_reviews(name=name, urls=urls, driver_path=driver_path, limit=limit)

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
