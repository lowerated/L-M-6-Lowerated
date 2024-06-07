# Entity Class for Rating Reviews

The `Entity` class is designed to process and rate attributes of entities based on textual reviews. This class can handle reviews provided directly as a list of strings, or from files in CSV, Excel (XLSX), or TXT format. Additionally, it supports downloading review files from a URL.

## Prerequisites

Before using the `Entity` class, ensure you have the required libraries installed:

- `pandas`
- `requests`

You can install these libraries using pip:

```bash
pip install pandas requests
```

## Setup

1. Ensure you have an `entities.json` file located at `./lowerated/rate/entities.json` with the structure defining default entities and their attributes.

2. Import the necessary modules and classes:

```python
import json
from typing import List
import pandas as pd
from lowerated.rate.utils import get_probabilities
import requests
```

3. Define the `Entity` class with its methods.

## Usage

### Initializing an Entity

Create an instance of the `Entity` class by specifying the entity name and optionally its attributes:

```python
entity_name = "Product"
attributes = ["Quality", "Value for Money", "Durability"]
product_entity = Entity(entity_name, attributes)
```

### Example 1: Using a List of Reviews

Rate the attributes of an entity using a list of textual reviews:

```python
reviews_list = ["Great product!", "Not worth the price.", "Excellent quality."]
openai_key = "your-openai-api-key"
probabilities = product_entity.rate(reviews=reviews_list, openai_key=openai_key)
print(probabilities)
```

### Example 2: Using a File Path

Rate the attributes of an entity using a file containing reviews. Supported file formats are CSV, Excel (XLSX), and TXT.

```python
file_path = "reviews.csv"  # Can be .csv, .xlsx, or .txt
openai_key = "your-openai-api-key"
probabilities = product_entity.rate(file_path=file_path, openai_key=openai_key)
print(probabilities)
```

### Example 3: Using a Download Link

Rate the attributes of an entity using a URL to download the file containing reviews:

```python
download_link = "https://example.com/reviews.xlsx"  # Can be .csv, .xlsx, or .txt
openai_key = "your-openai-api-key"
probabilities = product_entity.rate(download_link=download_link, openai_key=openai_key)
print(probabilities)
```

### Class and Method Details

#### `Entity` Class

- **Constructor**: Initializes an `Entity` instance.

  ```python
  def __init__(self, name, attributes=None):
  ```

- **Methods**:
  - `__str__`: Returns a string representation of the entity.
  - `get_attributes`: Returns the attributes of the current entity.
  - `get_entities`: Returns all available default entities.
  - `get_entity_attributes`: Returns the attributes of the specified entity.
  - `rate`: Rates the attributes of the entity based on reviews provided directly, from a file path, or a download link.

### JSON File Structure

Ensure the `entities.json` file has the following structure:

```json
{
  "Product": {
    "attributes": ["Quality", "Value for Money", "Durability"]
  },
  "Service": {
    "attributes": ["Customer Service", "Efficiency", "Cost"]
  }
}
```

### Notes

- The `rate` method returns probabilities as a JSON object with attributes and their values.
- Make sure the `get_probabilities` function is defined in `lowerated/rate/utils.py`.
