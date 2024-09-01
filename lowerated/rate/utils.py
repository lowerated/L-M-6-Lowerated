import torch
from transformers import BertTokenizer, BertForTokenClassification, pipeline
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Dict, List
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from typing import List, Dict, Optional, Any
import time
from selenium.common.exceptions import (NoSuchElementException, 
                                        TimeoutException, 
                                        ElementClickInterceptedException, 
                                        ElementNotInteractableException, 
                                        StaleElementReferenceException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from urllib.parse import urlparse


# Load models and tokenizer
aspect_model = BertForTokenClassification.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')
aspect_tokenizer = BertTokenizer.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')
sentiment_classifier = pipeline("zero-shot-classification", model="Lowerated/lm6-deberta-v3-topic-sentiment")

# Define the label mapping
label_columns = ['Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions']

def get_weights(entity: str, entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Retrieve the weights for each attribute of the given entity.

    Args:
        entity (str): The name of the entity (e.g., 'Movie').
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: A dictionary of attribute weights for the entity.
    """
    return entity_data.get(entity, {}).get('weights', {label: 1 for label in label_columns})

def rolling_mean_update(current_mean: float, new_value: float, count: int) -> float:
    """
    Description:
        Update the rolling mean with a new value.

    Args:
        current_mean (float): The current mean value.
        new_value (float): The new value to incorporate into the rolling mean.
        count (int): The number of data points considered so far.

    Return:
        float: The updated rolling mean.
    """
    if abs(new_value - current_mean) == 0:
        return current_mean
    updated_mean = ((current_mean * count) + new_value) / (count + 1)
    # Ensure the updated mean does not exceed 10
    return max(0, min(10, updated_mean))

def predict_snippet(review: str, aspect: str) -> List[str]:
    """
    Description:
        Predict and extract snippets from a review that are relevant to a specific aspect.

    Args:
        review (str): The text of the review.
        aspect (str): The aspect (e.g., 'Story', 'Cinematography') for which snippets are being extracted.

    Return:
        List[str]: A list of snippets relevant to the aspect.
    """
    model = aspect_model
    tokenizer = aspect_tokenizer
    model.eval()

    inputs = tokenizer.encode_plus(
        review,
        aspect,
        add_special_tokens=False,
        max_length=256,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation='longest_first'
    )
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    predictions = torch.argmax(logits, dim=2).flatten().tolist()
    new_predictions = predictions.copy()
    tokens = tokenizer.convert_ids_to_tokens(input_ids.flatten().tolist())
    
    snippets = []
    snippet = []
    i = 0
    for token, label in zip(tokens, predictions):
        if label == 1:
            new_predictions[i] = 1
            snippet.append(token)
        elif label == 0 and i > 0 and i + 1 < len(tokens) and predictions[i - 1] == 1 and predictions[i + 1] == 1:
            new_predictions[i] = 1
            snippet.append(token)
        elif len(snippet):
            snippets.append(' '.join(snippet))
            snippet = []
        i += 1

    for i in range(1, len(new_predictions) - 2):
        if new_predictions[i] == 0 and new_predictions[i+1] == 0 and new_predictions[i-1] == 1 and new_predictions[i+2] == 1:
            new_predictions[i] = 1
            new_predictions[i+1] = 1

    return snippets

def get_sentiment_score(snippet: str, aspect: str) -> float:
    """
    Description:
        Determine the sentiment score of a snippet for a specific aspect.

    Args:
        snippet (str): The text snippet related to an aspect.
        aspect (str): The aspect being analyzed.

    Return:
        float: The sentiment score scaled between 0 and 10.
    """
    positive_label = f"{aspect} positive"
    negative_label = f"{aspect} negative"
    sentiment_result = sentiment_classifier(snippet, [positive_label, negative_label])
    positive_score = sentiment_result['scores'][0]
    negative_score = sentiment_result['scores'][1]
    scaled_score = ((positive_score - negative_score + 1) / 2) * 10  # Already scaled to 0-10

    # Ensure the sentiment score does not exceed 10
    return max(0, min(10, scaled_score))

def compute_overall_rating(predictions: np.ndarray, weights: Dict[str, float]) -> float:
    """
    Description:
        Compute the overall rating for an entity by applying weights to the aspect predictions.

    Args:
        predictions (np.ndarray): Array of sentiment scores for each aspect.
        weights (Dict[str, float]): A dictionary of weights for each aspect.

    Return:
        float: The overall weighted rating.
    """
    filtered_predictions = []
    filtered_weights = []

    for i, pred in enumerate(predictions):
        if pred != 0:
            filtered_predictions.append(pred)
            filtered_weights.append(weights[label_columns[i]])

    if not filtered_predictions:
        return 0.0

    weighted_sum = sum(pred * weight for pred, weight in zip(filtered_predictions, filtered_weights))
    total_weight = sum(filtered_weights)
    return max(0, min(10, weighted_sum / total_weight))  # Clamp the overall rating between 0 and 10

def get_rating(reviews: List[str], entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Calculate the sentiment ratings for a list of reviews and compute an overall rating.

    Args:
        reviews (List[str]): A list of review texts.
        entity (str): The name of the entity (e.g., 'Movie').
        attributes (List[str]): A list of attributes/aspects to rate.
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: A dictionary of sentiment scores for each aspect, including the overall 'LM6' rating.
    """
    try:
        all_scores = {attribute: [] for attribute in attributes}

        for review in tqdm(reviews):
            # Split review into sentences
            sentences = sent_tokenize(review)
            for sentence in sentences:
                for aspect in attributes:
                    snippets = predict_snippet(sentence, aspect)
                    for snippet in snippets:
                        score = get_sentiment_score(snippet, aspect)
                        all_scores[aspect].append(score)

        probabilities = {attribute: np.mean(scores) if scores else 0.0 for attribute, scores in all_scores.items()}

        overall_rating = compute_overall_rating(
            np.array([probabilities[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        probabilities['LM6'] = overall_rating

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}

def update_rating_with_new_review(review: str, current_ratings: Dict[str, float], count: int, entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Update the current sentiment ratings with a new review. If the previous value for an aspect is zero,
        it calculates a normal mean instead of using a rolling mean.

    Args:
        review (str): The new review text.
        current_ratings (Dict[str, float]): The current ratings for each attribute.
        count (int): The number of reviews considered so far.
        entity (str): The name of the entity (e.g., 'Movie').
        attributes (List[str]): A list of attributes/aspects to rate.
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: The updated ratings for each attribute, including the overall 'LM6' rating.
    """
    try:
        sentences = sent_tokenize(review)
        for sentence in sentences:
            for aspect in attributes:
                snippets = predict_snippet(sentence, aspect)
                for snippet in snippets:
                    score = get_sentiment_score(snippet, aspect)
                    if current_ratings[aspect] == 0:
                        # If the previous rating was zero, take the new score directly
                        current_ratings[aspect] = score
                    else:
                        # Use rolling mean update if the previous rating is not zero
                        current_ratings[aspect] = rolling_mean_update(current_ratings[aspect], score, count)
                    
                    # Ensure the updated rating does not exceed 10
                    current_ratings[aspect] = max(0, min(10, current_ratings[aspect]))

        overall_rating = compute_overall_rating(
            np.array([current_ratings[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        current_ratings['LM6'] = overall_rating

        return current_ratings

    except Exception as e:
        print(f"Error in updating ratings: {e}")
        return current_ratings


# Function to get imdb rating of a specific movie or list of movies
def get_imdb_ratings(name: str = None, urls: list = None, driver_path: str = None) -> list:
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

    # Initialize WebDriver with the specified or default driver path
    driver = webdriver.Chrome(service=Service(driver_path)) if driver_path else webdriver.Chrome()

    results = []

    # If movie URLs are provided, go directly to each movie page
    if urls:
        for movie_url in urls:
            driver.get(movie_url)
            time.sleep(3)

            # Scrape the IMDb rating and movie title from the IMDb page
            try:
                imdb_rating = driver.find_element(By.CSS_SELECTOR, "span.sc-eb51e184-1.ljxVSS").text  # Updated CSS selector for IMDb rating
                movie_title = driver.find_element(By.CSS_SELECTOR, "h1").text
                print(f"Movie Title: {movie_title}")
                print(f"IMDb Rating: {imdb_rating}")
            except Exception as e:
                print(f"Error extracting IMDb rating from {movie_url}: {e}")
                imdb_rating = "Not Found"
                movie_title = movie_url

            # Append the result to the list
            results.append({"Movie Title": movie_title, "IMDb Rating": imdb_rating})

    elif name:
        # Open IMDb website and search for the movie if no URL is provided
        driver.get("https://www.imdb.com/")
        time.sleep(2)

        # Enter the movie name in the IMDb search bar and submit the search
        search_input = driver.find_element(By.ID, "suggestion-search")
        search_input.send_keys(name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(3)

        # Process the search results to find the best match using fuzzy logic
        try:
            # Collect all search result links
            results_links = driver.find_elements(By.CSS_SELECTOR, "ul.ipc-metadata-list li a")

            # If no results found, return "Not Found"
            if not results_links:
                print("No search results found.")
                driver.quit()
                return [{"Movie Title": name, "IMDb Rating": "Not Found"}]

            best_match = None
            highest_ratio = 0

            # Compare each result with the provided movie name using fuzzy matching
            for result_link in results_links:
                result_title = result_link.text.strip()
                similarity_ratio = fuzz.ratio(name.lower(), result_title.lower())

                # Keep track of the highest matching result
                if similarity_ratio > highest_ratio:
                    highest_ratio = similarity_ratio
                    best_match = result_link

                # If a match with similarity above 80% is found, break early
                if highest_ratio >= 80:
                    break

            # Click on the best matching result if the similarity is at least 70%
            if best_match and highest_ratio >= 70:
                best_match.click()
                time.sleep(3)
            else:
                print("No close match found. Please make sure you've written the correct spelling.")
                driver.quit()
                return [{"Movie Title": name, "IMDb Rating": "Not Found"}]

        except Exception as e:
            print("Error locating the movie:", e)
            driver.quit()
            return [{"Movie Title": name, "IMDb Rating": "Not Found"}]

        # Scrape the IMDb rating from the movie's IMDb page
        try:
            imdb_rating = driver.find_element(By.CSS_SELECTOR, "span.sc-eb51e184-1.ljxVSS").text  # Updated CSS selector for IMDb rating
            movie_title = driver.find_element(By.CSS_SELECTOR, "h1").text
            print(f"Movie Title: {movie_title}")
            print(f"IMDb Rating: {imdb_rating}")
        except Exception as e:
            print("Error extracting IMDb rating:", e)
            imdb_rating = "Not Found"
            movie_title = name

        # Append the result to the list
        results.append({"Movie Title": movie_title, "IMDb Rating": imdb_rating})
    
    else:
        print("Please provide either a movie name or a list of movie URLs.")
        driver.quit()
        return [{"Movie Title": "Not Provided", "IMDb Rating": "Not Provided"}]

    # Close the WebDriver
    driver.quit()

    # Return the scraped data as a list of dictionaries
    return results


# Function to get rotten tomatoes ratings of a specific movie or list of movies
def get_rotten_tomatoes_ratings(
    urls: Optional[List[str]] = None,
    name: Optional[str] = None,
    config: Optional[Dict[str, Dict[str, Any]]] = None,
    driver_path: Optional[str] = None
) -> List[Dict[str, Any]]:
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

    # Default configuration for scraping
    default_config = {
        'critics_selector': {'by': 'attrs', 'value': {"slot": "criticsScore"}},
        'audience_selector': {'by': 'attrs', 'value': {"slot": "audienceScore"}}
    }

    # Update default configuration with any provided config
    config = config or {}
    scrape_config = {**default_config, **config}

    # Initialize WebDriver with the specified or default path
    if driver_path:
        driver = webdriver.Chrome(service=Service(driver_path))
    else:
        driver = webdriver.Chrome()

    if name:
        # Search for the movie by name
        driver.get("https://www.rottentomatoes.com/")
        time.sleep(1)

        # Locate the search input element
        search_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search']")
        search_input.send_keys(name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Find all movie results
        results_elements = driver.find_elements(By.CSS_SELECTOR, "search-page-media-row a")

        # Extract titles and URLs
        titles_urls = [(element.text, element.get_attribute("href")) for element in results_elements]

        # Apply fuzzy matching to find the best match
        best_match = None
        highest_ratio = 0
        for title, url in titles_urls:
            ratio = fuzz.ratio(name.lower(), title.lower())
            if ratio > highest_ratio and ratio >= 70:  # Match threshold set at 70%
                highest_ratio = ratio
                best_match = url

        if not best_match:
            driver.quit()
            print(f"No close match found for '{name}'. Please try a different name.")
            return [{"Movie Title": name, "Critics Score": "Not Found", "Audience Score": "Not Found"}]

        urls = [best_match]  # Use the best match URL for scraping

    results = []

    for url in urls:
        driver.get(url)
        time.sleep(1)

        # Extract the movie title directly from the URL
        movie_slug = url.split('/m/')[-1]  # Get the last part after "/m/"
        movie_title = movie_slug.replace('_', ' ').title()  # Replace underscores and capitalize words

        # Extract the page source for further parsing
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract critics score using configuration
        critics_selector = scrape_config['critics_selector']
        critics = soup.find(attrs=critics_selector['value'])
        critics_score = critics.get_text().strip() if critics else 'Not Found'

        # Extract audience score using configuration
        audience_selector = scrape_config['audience_selector']
        audience = soup.find(attrs=audience_selector['value'])
        audience_score = audience.get_text().strip() if audience else 'Not Found'

        # Convert the scores to a scale out of 10
        try:
            critics_score = round(int(critics_score.strip('%')) / 10, 1) if critics_score != 'Not Found' else 'Not Found'
        except ValueError:
            critics_score = 'Not Found'

        try:
            audience_score = round(int(audience_score.strip('%')) / 10, 1) if audience_score != 'Not Found' else 'Not Found'
        except ValueError:
            audience_score = 'Not Found'

        # Save the results in a dictionary
        result = {
            "Movie Title": movie_title,
            "Critics Score": critics_score,
            "Audience Score": audience_score
        }
        results.append(result)

    driver.quit()

    # Output the results in a formatted manner
    for result in results:
        print(f"Movie Title:   {result['Movie Title']}")
        print(f"Critics Score: {result['Critics Score']}")
        print(f"Audience Score: {result['Audience Score']}")

    return results


# Function to scrap audience reviews from rotten tomatoes
def get_audience_reviews_rotten_tomatoes(
    urls: Optional[List[str]] = None,
    name: Optional[str] = None,
    driver_path: Optional[str] = None,
    review_limit: Optional[int] = None
) -> List[Dict[str, Any]]:
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

    # Initialize WebDriver with the specified or default path
    if driver_path:
        driver = webdriver.Chrome(service=Service(driver_path))
    else:
        driver = webdriver.Chrome()

    if name:
        # Navigate to Rotten Tomatoes and search for the movie by name
        driver.get("https://www.rottentomatoes.com/")
        time.sleep(1)

        # Locate and interact with the search input element
        search_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search']")
        search_input.send_keys(name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Retrieve movie results
        results_elements = driver.find_elements(By.CSS_SELECTOR, "search-page-media-row a")

        # Extract titles and URLs
        titles_urls = [(element.text, element.get_attribute("href")) for element in results_elements]

        # Apply fuzzy matching to find the best match
        best_match = None
        highest_ratio = 0
        for title, url in titles_urls:
            ratio = fuzz.ratio(name.lower(), title.lower())
            if ratio > highest_ratio and ratio >= 70:  # Match threshold set at 70%
                highest_ratio = ratio
                best_match = url

        if not best_match:
            driver.quit()
            print(f"No close match found for '{name}'. Please try a different name.")
            return [{"Movie Title": name, "Audience Reviews": "Not Found"}]

        urls = [best_match]  # Use the best match URL for scraping

    results = []

    for url in urls:
        driver.get(url)
        time.sleep(1)

        # Extract the movie title directly from the URL
        movie_slug = url.split('/m/')[-1]  # Get the last part after "/m/"
        movie_title = movie_slug.replace('_', ' ').title()  # Replace underscores and capitalize words

        # Scroll to load the audience reviews section
        driver.execute_script("window.scrollBy(0, 1100);")
        time.sleep(1)

        # Save the total number of reviews available
        try:
            total_audience_element = driver.find_element(By.XPATH, '//*[@id="modules-wrap"]/section[2]/div[1]/rt-link')
        except NoSuchElementException:
            print('No audience reviews found.')
            total_audience_element = None
                    
        if total_audience_element:
            total_text = total_audience_element.text
            
            match = re.search(r'\((\d+)\+', total_text)
            if match:
                total_reviews = int(match.group(1))  
            else:
                match = re.search(r'\((\d+)\)', total_text)
                if match:
                    total_reviews = int(match.group(1))  
                else:
                    total_reviews = None
                    print('Number of reviews not found using regex.')    

        # Open the review page if reviews are available
        if total_reviews:
            driver.get(f'https://www.rottentomatoes.com/m/{movie_slug}/reviews?type=user')
            time.sleep(1)

            current_reviews = []
            reviews_to_collect = min(total_reviews - 1, review_limit) if review_limit else total_reviews - 1
        
            # Iterate through the number of reviews
            for review_num in range(1, reviews_to_collect + 1):
                
                # Click "Load More" button after every 20 reviews
                if review_num % 20 == 0:
                    try:
                        print(f"Loading more reviews. Total reviews collected: {review_num}", end=" ")
                        more_reviews_button = driver.find_element(By.XPATH, '//*[@id="reviews"]/div[2]/rt-button')
                        more_reviews_button.click()
                        time.sleep(2)
                    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
                        print(f"Load more button not found. Stopping review collection.")
                        break           

                # Extract review text
                try:                                                                                                    
                    review_element = driver.find_element(By.XPATH, f'//*[@id="reviews"]/div[1]/div[{review_num}]/div[2]/drawer-more/p')
                    review_text = review_element.text
                    
                    print(f"Review {review_num}: {review_text[:75]}...")
                    
                except (NoSuchElementException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException):
                    review_text = 'Not Found'
                    print(f"Review {review_num} not found.")
                    time.sleep(2)

                driver.execute_script("window.scrollBy(0, 150);")
                time.sleep(1)
                        
                current_review = {
                    'ReviewID': review_num,
                    'ReviewText': review_text,
                }
                        
                current_reviews.append(current_review)

            # Create JSON document for the movie
            result = {
                "Movie Title": movie_title,
                "Audience Reviews": current_reviews
            }
                    
            results.append(result)
            
            print(f'Total reviews collected: {review_num} for movie: {movie_title}')
        
    driver.quit()
    return results


#   Function to scrap critics reviews from Rotten Tomatoes
def get_critics_reviews_rotten_tomatoes(
    urls: Optional[List[str]] = None,
    name: Optional[str] = None,
    driver_path: Optional[str] = None,
    review_limit: Optional[int] = None
) -> List[Dict[str, Any]]:
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

    # Initialize WebDriver with the specified or default path
    if driver_path:
        driver = webdriver.Chrome(service=Service(driver_path))
    else:
        driver = webdriver.Chrome()

    ExceptionUrlList = []
    results = []

    try:
        if name:
            # Search for the movie by name
            driver.get("https://www.rottentomatoes.com/")
            time.sleep(1)

            # Locate and interact with the search input element
            search_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search']")
            search_input.send_keys(name)
            search_input.send_keys(Keys.RETURN)
            time.sleep(2)

            # Retrieve movie results
            results_elements = driver.find_elements(By.CSS_SELECTOR, "search-page-media-row a")

            # Extract titles and URLs
            titles_urls = [(element.text, element.get_attribute("href")) for element in results_elements]

            # Apply fuzzy matching to find the best match
            best_match = None
            highest_ratio = 0
            for title, url in titles_urls:
                ratio = fuzz.ratio(name.lower(), title.lower())
                if ratio > highest_ratio and ratio >= 70:  # Match threshold set at 70%
                    highest_ratio = ratio
                    best_match = url

            if not best_match:
                driver.quit()
                return [{"Movie Title": name, "Critic Reviews": "Not Found"}]

            urls = [best_match]  # Use the best match URL for scraping

        for url in urls:
            movie_id = url.split('/')[-1]

            try:
                driver.get(url)
                time.sleep(5)
                driver.execute_script("window.scrollBy(0, 1000);")

                # Save the total number of reviews available
                try:
                    TotalCritics = driver.find_element(By.XPATH, '//*[@id="modules-wrap"]/div[4]/section/div[1]/rt-link')
                except NoSuchElementException:
                    try:
                        TotalCritics = driver.find_element(By.XPATH, '//*[@id="modules-wrap"]/div[5]/section/div[1]/rt-link')
                    except NoSuchElementException:
                        try:
                            TotalCritics = driver.find_element(By.XPATH, '//*[@id="modules-wrap"]/div[3]/section/div[1]/rt-link')
                        except NoSuchElementException:
                            try:
                                TotalCritics = driver.find_element(By.XPATH, '//*[@id="modules-wrap"]/div[2]/section/div[1]/rt-link')
                            except NoSuchElementException:
                                TotalCritics = None

                if TotalCritics:
                    total_text = TotalCritics.text
                    match = re.search(r'View All \((\d+)\)', total_text)
                    num_reviews = int(match.group(1)) if match else None
                else:
                    num_reviews = None

                # Open the review page if reviews are available
                if num_reviews:
                    parsed_url = urlparse(url)
                    movie_name = parsed_url.path.split('/m/')[-1]

                    try:
                        driver.get(f'https://www.rottentomatoes.com/m/{movie_name}/reviews')
                        time.sleep(3)

                        current_reviews = []
                        num_reviews = min(num_reviews, review_limit) if review_limit else num_reviews

                        # Iterate through the number of reviews
                        for review_num in range(1, num_reviews + 1):
                            # Click "Load More" button after every 20 reviews
                            if review_num % 20 == 0:
                                try:
                                    more_reviews_button = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, '//*[@id="reviews"]/div[2]/rt-button'))
                                    )
                                    more_reviews_button.click()
                                    time.sleep(1)
                                except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
                                    continue 
                            
                            # Extract review text
                            try:
                                review_text = driver.find_element(By.XPATH, f'//*[@id="reviews"]/div[1]/div[{review_num}]/div[2]').text
                            except (NoSuchElementException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException):
                                review_text = 'Not Found'
                            
                            current_review = {
                                'ReviewID': review_num,
                                'ReviewText': review_text,
                            }
                            
                            current_reviews.append(current_review)
                            
                            if len(current_reviews) >= review_limit:
                                break

                        current_movie = {
                            "_id": movie_id,
                            "Critic Reviews": current_reviews
                        }
                        
                        results.append(current_movie)

                    except TimeoutException:
                        ExceptionUrlList.append(url)
                
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    finally:
        driver.quit()

    # Print the results
    for result in results:
        print(f"Movie ID: {result['_id']}")
        for review in result["Critic Reviews"]:
            print(f"Review ID: {review['ReviewID']}")
            print(f"Review Text: {review['ReviewText']}")
            print("-" * 80)

    return results




#   Function to get imdb reviews
def get_imdb_reviews(name: str = None, urls: list = None, driver_path: str = None, limit: int = 10) -> list:
    """
    Description:
        Scrape IMDb user reviews by searching for the movie by providing its name or a list of URLS.

    Args:
        name: str - The name of the movie to search for on IMDb. Ignored if imdb_urls are provided.
        urls: list - A list of IMDb URLs to the movie's reviews page. Overrides movie_name if provided.
        driver_path: str - Path to the ChromeDriver executable. If None, the system's default driver will be used.
        limit: int - The number of reviews to scrape from each URL or search result. Default is 10.

    Returns:
        list - A list of dictionaries containing the movie titles and their IMDb user reviews.
    """
    driver = webdriver.Chrome(service=Service(driver_path)) if driver_path else webdriver.Chrome()

    results = []

    def load_more_reviews():
        """Helper function to click 'Load More' to load additional reviews."""
        try:
            load_more_button = driver.find_element(By.ID, "load-more-trigger")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            load_more_button.click()
            time.sleep(3)  # Wait for more reviews to load
        except Exception as e:
            print("No 'Load More' button or reached the end of reviews.", e)

    def extract_reviews(num_needed):
        """Helper function to extract reviews from the current page."""
        reviews_extracted = []
        while len(reviews_extracted) < num_needed:
            current_reviews = driver.find_elements(By.CSS_SELECTOR, "div.review-container div.text.show-more__control")
            for review in current_reviews:
                review_text = review.text
                if review_text not in reviews_extracted:
                    reviews_extracted.append(review_text)
                    if len(reviews_extracted) >= num_needed:
                        break
            if len(reviews_extracted) < num_needed:
                load_more_reviews()
            else:
                break
        return reviews_extracted

    def fuzzy_match_movie(search_results, user_query):
        """Fuzzy matches the movie name from search results to find the best match using fuzzywuzzy."""
        movie_titles = [result.text for result in search_results]
        best_match = None
        highest_ratio = 0
        
        for title in movie_titles:
            ratio = fuzz.ratio(user_query.lower(), title.lower())
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = title
        
        return best_match

    if urls:
        # Scrape reviews directly from provided URLs
        for imdb_url in urls:
            driver.get(imdb_url)
            time.sleep(3)

            try:
                # Scrape the movie title
                movie_title = driver.find_element(By.CSS_SELECTOR, 'h1').text

                # Extract reviews and load more if needed
                reviews = extract_reviews(limit)

                for review_text in reviews[:limit]:
                    results.append({"Movie Title": movie_title, "Review": review_text})

            except Exception as e:
                print(f"Error during scraping for URL {imdb_url}: {e}")

    elif name:
        # Search IMDb for the movie and scrape reviews from the search result
        driver.get("https://www.imdb.com/")
        time.sleep(2)

        # Enter the movie name in the IMDb search bar and submit the search
        search_input = driver.find_element(By.ID, "suggestion-search")
        search_input.send_keys(name)
        search_input.send_keys(Keys.RETURN)
        time.sleep(3)

        try:
            # Get all search result titles
            search_results = driver.find_elements(By.CSS_SELECTOR, "ul.ipc-metadata-list li a")

            # Use fuzzy logic to find the closest match to the movie name
            best_match = fuzzy_match_movie(search_results, name)
            if not best_match:
                print(f"No close match found for '{name}'.")
                driver.quit()
                return []

            # Click on the best matching movie result
            for result in search_results:
                if result.text == best_match:
                    result.click()
                    break

            time.sleep(3)
            
            # Scrape the movie title
            movie_title = driver.find_element(By.CSS_SELECTOR, 'h1').text
            
            # Scroll to the "User reviews" button
            user_reviews_button = driver.find_element(By.CSS_SELECTOR, "a[href*='reviews?ref_=tt_urv']")
            driver.execute_script("arguments[0].scrollIntoView(true);", user_reviews_button)
            time.sleep(2)
            
            # Click the "User reviews" button
            user_reviews_button.click()
            time.sleep(3)

            # Extract reviews and load more if needed
            reviews = extract_reviews(limit)

            for review_text in reviews[:limit]:
                results.append({"Movie Title": movie_title, "Review": review_text})

        except Exception as e:
            print(f"Error during search and navigation for {limit}: {e}")
    
    else:
        print("Error: Either a movie name or a list of IMDb URLs must be provided.")
        driver.quit()
        return []

    driver.quit()
    return results