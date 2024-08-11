
# Lowerated Rating Algorithm - Architecture

## Overview

The Lowerated Rating Algorithm is designed to provide accurate and unbiased ratings for movies and other entities. The architecture leverages machine learning models to extract and analyze sentiments from textual reviews, focusing on predefined attributes that are critical for assessing the quality of the entity.

### Components

The architecture consists of several key components:

1. **Entity Class**: 
   - Central to the algorithm, representing any item that can be rated.
   - Houses the attributes and methods to calculate ratings based on textual reviews.
   - Supports both predefined and custom attributes.

2. **Sentiment Analysis Models**:
   - **Aspect Model**: A BERT-based model fine-tuned for aspect extraction from reviews. Identifies relevant snippets within the text related to specific attributes.
   - **Sentiment Classifier**: A DeBERTa-based model designed to classify the sentiment (positive/negative) of the extracted snippets.

3. **Rolling Mean Calculation**:
   - Uses a rolling mean to update ratings as new reviews are added.
   - Incorporates a threshold to ignore insignificant changes.
   - If a previous aspect score was zero, a normal mean is applied instead of a rolling mean.

### Workflow

1. **Initialization**:
   - The `Entity` class is initialized with a name (e.g., "Movie") and attributes (e.g., "Cinematography", "Story").
   - The entity can either use predefined attributes or custom ones provided by the user.

2. **Review Processing**:
   - Reviews can be input directly, read from a file, or downloaded from a URL.
   - The reviews are split into sentences, and the aspect model predicts snippets relevant to each attribute.
   - The sentiment classifier assigns a sentiment score to each snippet.

3. **Rating Calculation**:
   - For each review, sentiment scores for all relevant attributes are calculated and averaged.
   - The overall rating (LM6) is computed using weighted averages of the attribute scores.
   - If new reviews are added, the ratings are updated using the rolling mean approach, except for attributes with a previous score of zero.

### Models and Techniques

- **BERT for Token Classification**:
  - Used for aspect-based extraction, identifying parts of the text that discuss specific attributes.
  
- **DeBERTa for Zero-Shot Classification**:
  - Employed to classify sentiment on the extracted snippets without needing task-specific labels.

### Key Files

1. **utils.py**:
   - Contains utility functions for sentiment scoring, rolling mean calculations, and rating updates.
   - Functions like `get_sentiment_score`, `compute_overall_rating`, `rolling_mean_update`, and `get_rating` are implemented here.

2. **entity.py**:
   - Defines the `Entity` class, which encapsulates the attributes, methods for rating calculations, and rating updates.
   - Provides the structure for how entities are initialized and rated.

### Data Flow

1. **Input**: Reviews (textual data) provided as a list, file, or URL.
2. **Processing**:
   - Aspect extraction from reviews.
   - Sentiment scoring for extracted snippets.
   - Rolling mean calculations for updating ratings.
3. **Output**: Ratings for each attribute and an overall score (LM6).

### Extensibility

- The system is designed to be extensible:
  - **Custom Entities**: Users can define new entities with any number of attributes.
  - **Model Fine-Tuning**: The models can be further fine-tuned to improve accuracy for specific domains.

### Conclusion

The Lowerated Rating Algorithm is a robust and flexible system designed to deliver accurate ratings across a variety of domains. By leveraging cutting-edge NLP models and a well-thought-out architecture, it provides a reliable method for evaluating entities based on textual reviews.
