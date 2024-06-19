# Lowerated's Rating Algorithm

<p align="center">
    <img src="./media/logos/main-logo-black-background.jpeg" alt="Logo" width="200">
</p>

<h3 align="center">
    <strong>The Best Way to Rate  & Recommend Anything</strong>
</h3>

- An algorithm that provides accurate ratings for any entity.
- Uses diverse sources: reviews, links, documents, and other resources.
- Completely unbiased.
- Combines AI and human evaluation to determine the true rating of an entity.

### What is an Entity?

- Anything that can be rated.
- Examples include films, cars, books, music, furniture, even your partner.

### How Does It Work?

- We have predefined research attributes that, when measured, give a comprehensive understanding of the item. Let's use a movie as an example.

#### Movie Rating Attributes

We evaluate a movie based on seven attributes:

1. **Cinematography** - Visual appeal and camera work.
2. **Direction** - How well the director conveys the story.
3. **Story** - Plot coherence and engagement.
4. **Characters** - Depth and development of characters.
5. **Production Design** - Quality of the sets and overall look.
6. **Unique Concept** - Originality of the idea.
7. **Emotions** - Emotional impact on the audience.

We gather reviews from multiple critics and users. Our AI extracts information from the text inputs and assigns numerical values to each attribute. This process is repeated for all reviews, and we average the results.

Each attribute is given a percentage value from 0-100%, reflecting its presence in the movie.

We have identified key attributes for multiple entities, detailed in the listed in [entities & attributes](./docs/rate/entities_attributes.md)

## Can we add more attributes?

Yes, 7 is the standard for all the default entities given, you can create your own entities and assign them as many attributes you want.

## How do I use it?

Check Out the steps to use Lowerated [here](./docs/rate/how_to_use.md)

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
entity_name = "Product"
attributes = find_attributes(entity_name)
print(attributes)
```

### Initializing an Available Entity or Creating Custom Entity

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

## Example Output

```
To rate the reviews, the algorithm will cost: 0.0001195 $

{'Cinematography': 0.7, 'Direction': 0.0, 'Story': 0.5, 'Characters': 0.8, 'Production Design': 0.9, 'Unique Concept': 0.0, 'Emotions': -0.4}
```

### Notes

- The `rate` method returns probabilities as a JSON object with attributes and their values.
- Make sure the `get_probabilities` function is defined in `lowerated/rate/utils.py`.

### Lisence

[Apache 2.0](./LICENSE)

Copyright (2024) FACT-RATED MEDIA (PVT-LTD)
