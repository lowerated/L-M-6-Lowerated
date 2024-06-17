import openai
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


def bring_web_reviews(keywords: str):
    """
    Using Keywords given by user, this function extracts content (reviews, comments, etc) from all over the web related to those keywords 
    """

    pass


def read_reviews(file_path: str = None, download_link: str = None, review_column: str = None):
    """
    Reading Reviews from:
        1. File as CSV or Excel
        2. Downloadable link
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
