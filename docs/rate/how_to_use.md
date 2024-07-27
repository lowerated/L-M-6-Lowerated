# Entity Class for Rating Reviews

The `Entity` class is designed to process and rate attributes of entities based on textual reviews. This class can handle reviews provided directly as a list of strings, or from files in CSV, Excel (XLSX), or TXT format. Additionally, it supports downloading review files from a URL.

## Prerequisites

Before using the `Entity` class, ensure you have the required libraries installed:

- `lowerated`

You can install these libraries using pip:

```bash
pip install lowerated
```

## Setup

1. Import the necessary modules and classes:

```python
from lowerated.rate import Entity
from lowerated.rate.utils import entities, find_attributes
```

3. Define the `Entity` class with its methods.


## Usage

### See Available Entities & their Attributes

Get a list of available entities and their attributes:

```python
entities = entities()
print(entities)
```

To see a specific entity's attributes, use the code below:

```python
entity_name = "Movie"
attributes = find_attributes(entity_name)
print(attributes)
```

### Initializing an Available Entity or Creating Custom Entity

Create an instance of the `Entity` class by specifying the entity name and optionally its attributes:

```python
entity_name = "Movie"
attributes = ['Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions']
movie_entity = Entity(entity_name, attributes)
```

### Example 1: Using a List of Reviews

Rate the attributes of an entity using a list of textual reviews:

```python
reviews_list = ["Great movie!", "Not worth the price.", "Excellent cinematography."]
rating = movie_entity.rate(reviews=reviews_list, openai_key=openai_key)
print(rating)
```

### Example 2: Using a File Path

Rate the attributes of an entity using a file containing reviews. Supported file formats are CSV, Excel (XLSX), and TXT.

```python
file_path = "reviews.csv"  # Can be .csv, .xlsx, or .txt
rating = movie_entity.rate(file_path=file_path, openai_key=openai_key)
print(rating)
```

### Example 3: Using a Download Link

Rate the attributes of an entity using a URL to download the file containing reviews:

```python
download_link = "https://example.com/reviews.xlsx"  # Can be .csv, .xlsx, or .txt
rating = movie_entity.rate(download_link=download_link, openai_key=openai_key)
print(rating)
```

### Notes

- The `rate` method returns probabilities as a JSON object with attributes and their values.
- Make sure the `get_probabilities` function is defined in `lowerated/rate/utils.py`.

### Lisence

[Apache 2.0](./LICENSE)

Copyright (2024) FACT-RATED MEDIA (PVT-LTD)
