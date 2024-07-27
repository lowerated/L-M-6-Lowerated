from bs4 import BeautifulSoup
import numpy as np
import json
from typing import List, Dict
import requests
import pandas as pd


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
