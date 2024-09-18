from bs4 import BeautifulSoup
from typing import List, Dict
import requests
import pandas as pd
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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

def reviews_from_df(df, review_column):
    """
    If review column is given by user, we use that column else the first column of the dataframe
    """

    if review_column and df[review_column]:
        reviews = df[review_column]
    else:
        reviews = df.iloc[:, 0].tolist()

    return reviews


def read_reviews(file_path: str = None, download_link: str = None, review_column: str = None):
    """
    Reading Reviews from:
        1. File as CSV or Excel
        2. Downloadable link
    """

    if file_path is None and download_link is None:
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
                reviews = reviews_from_df(df=df, review_column=review_column)

            elif filename.endswith('.xlsx'):
                df = pd.read_excel(pd.compat.BytesIO(response.content))
                reviews = reviews_from_df(df=df, review_column=review_column)

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
            reviews = reviews_from_df(df=df, review_column=review_column)

        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            reviews = reviews_from_df(df=df, review_column=review_column)

        elif file_path.endswith('.txt'):
            with open(file_path, 'r') as file:
                reviews = file.readlines()
            # Remove any extra whitespace
            reviews = [review.strip() for review in reviews]
        else:
            print("Invalid File Path")
            return


def bring_web_reviews(keywords: List[str]):
    """
    Using a list of keywords given by user, this function extracts content (reviews, comments, etc) 
    from all over the web related to those keywords and stores them in a JSON-like dictionary.

    Returns:
    {
        "keyword 1": [list of reviews related to keyword 1],
        "keyword 2": [list of reviews related to keyword 2]
    }
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    results = {}

    for keyword in keywords:
        search_query = f"{keyword.replace(' ', '+')}+reviews"
        url = f"https://www.google.com/search?q={search_query}"

        print(url)

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f'''Failed to retrieve content for keyword {
                  keyword}: {response.status_code}''')
            results[keyword] = []
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        review_snippets = []

        for div in soup.find_all('div', class_='BVG0Nb'):
            snippet = div.get_text()
            if snippet:
                review_snippets.append(snippet)

        results[keyword] = review_snippets

    return results


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
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Description:
        Scrapes audience reviews from Rotten Tomatoes based on provided URLs or by searching for a movie name.

    Args:
        urls: Optional[List[str]] - List of URLs to scrape reviews from.
        name: Optional[str] - Movie name to search and scrape reviews for.
        driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.
        limit: Optional[int] - Maximum number of reviews to scrape. If None, all available reviews will be collected.

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
            reviews_to_collect = min(total_reviews - 1, limit) if limit else total_reviews - 1
        
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
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Description:
        Scrapes critic reviews from Rotten Tomatoes based on provided URLs or by searching for a movie name.

    Args:
        urls: Optional[List[str]] - List of URLs to scrape reviews from.
        name: Optional[str] - Movie name to search and scrape reviews for.
        driver_path: Optional[str] - Path to the ChromeDriver executable. If None, the system's default driver will be used.
        limit: Optional[int] - Maximum number of reviews to scrape. If None, all available reviews will be collected.

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
                        num_reviews = min(num_reviews, limit) if limit else num_reviews

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
                            
                            if len(current_reviews) >= limit:
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
        Scrape IMDb user reviews by searching for the movie by providing its name or a list of URLs.

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
            

            # Correct XPath for the "User Reviews" button based on the image
            correct_button_xpath = '//*[@data-testid="UserReviews"]//a[contains(@href, "/reviews/")]'

            
            # Wait for the correct button to be present in the DOM
            correct_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, correct_button_xpath))
            )
            
            # Scroll down to the correct button
            driver.execute_script("arguments[0].scrollIntoView(true);", correct_button)
            
            # Wait until the correct button is clickable
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, correct_button_xpath))
            )
            
            # Click the correct button
            correct_button.click()
            time.sleep(3)
            print("Button clicked successfully.")

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

    # Close the driver
    driver.quit()

    # Print the results in a nicely formatted manner
    print(f"\n{'='*80}")
    print(f"Movie: {results[0]['Movie Title'] if results else 'No Reviews Found'}")
    print(f"Total Reviews Scraped: {min(len(results), 5)}")
    print(f"{'='*80}")
    
    # Only print the first 5 reviews
    for i, result in enumerate(results[:5], start=1):
        print(f"Review {i}:\n{result['Review']}\n{'-'*80}")

    return results