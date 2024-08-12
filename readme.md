# Lowerated's Rating Algorithm

<p align="center">
    <img src="./media/logos/main-logo-black-background.jpeg" alt="Logo" width="200">
</p>

<h3 align="center">
    <strong>The Best Way to Rate & Recommend Movies</strong>
</h3>
<div align="center">
<a  href="https://huggingface.co/Lowerated/lm6-movie-aspect-extraction-bert"
    ><img
      src="https://img.shields.io/badge/HuggingFace-Models-blue?logo=huggingface&style=flat-square"
      alt="Lowerated Models"
  /></a>
<a href="https://huggingface.co/Lowerated/lm6-deberta-v3-topic-sentiment"
    ><img
      src="https://img.shields.io/badge/DeBERTa-v3-blue?logo=huggingface&style=flat-square"
      alt="LM6 DeBERTa"
  /></a>
<a href="https://huggingface.co/datasets/Lowerated/lm6-movies-reviews-aspects"
    ><img
      src="https://img.shields.io/badge/HuggingFace-Datasets-blue?logo=huggingface&style=flat-square"
      alt="Lowerated Data"
  /></a>
<a
    href="https://www.youtube.com/playlist?list=PLK1glKdPynXxjvHrSJQiT46k1rdsFWwJf"
    ><img
      src="https://img.shields.io/youtube/views/PLK1glKdPynXxjvHrSJQiT46k1rdsFWwJf?label=YouTube%20Views&style=social"
      alt="YouTube Playlist"
  /></a>
</div>
<br />
<br />

- An algorithm that provides accurate ratings for any entity.
- Uses diverse sources: reviews, links, documents, and other resources.
- Completely unbiased.
- Combines AI and human evaluation to determine the true rating of an entity.

### What is an Entity?

- Anything that can be rated.
- Examples include films, cars, books, music, furniture, even your partner.
- In the case of Lowerated, we're dealing with "Movies".

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

We have identified key attributes for multiple entities, detailed in the listed [Entities & Attributes](./docs/rate/entities_attributes.md).

## How do I use it?

Check out the steps to use Lowerated [here](./docs/rate/how_to_use.md).

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

2. Define the `Entity` class with its methods.

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

### Initializing an Available Entity or Creating a Custom Entity

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
rating = movie_entity.rate(reviews=reviews_list)
print(rating)
```

### Example 2: Using a File Path

Rate the attributes of an entity using a file containing reviews. Supported file formats are CSV, Excel (XLSX), and TXT.

```python
file_path = "reviews.csv"  # Can be .csv, .xlsx, or .txt
rating = movie_entity.rate(file_path=file_path)
print(rating)
```

### Example 3: Using a Download Link

Rate the attributes of an entity using a URL to download the file containing reviews:

```python
download_link = "https://example.com/reviews.xlsx"  # Can be .csv, .xlsx, or .txt
rating = movie_entity.rate(download_link=download_link)
print(rating)
```

### License

[Apache 2.0](./LICENSE)

Copyright (2024) FACT-RATED MEDIA (PVT-LTD)
