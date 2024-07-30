import torch
from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Dict, List

# Load the fine-tuned model and tokenizer
model = DebertaV2ForSequenceClassification.from_pretrained('lowerated/deberta-v3-lm6')
tokenizer = DebertaV2Tokenizer.from_pretrained('lowerated/deberta-v3-lm6')

# Ensure the model is in evaluation mode
model.eval()

# Define the label mapping
label_columns = ['Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions']

def get_weights(entity: str, entity_data: Dict) -> Dict[str, float]:
    """
    Returns weights for the given entity.

    Args:
        entity (str): Name of the entity

    Returns:
        Dict[str, float]: Weights for each attribute
    """
    return entity_data.get(entity, {}).get('weights', {label: 1 for label in label_columns})

def rolling_mean_update(current_mean: float, new_value: float, count: int) -> float:
    """
    Updates the rolling mean with a new value.

    Args:
        current_mean (float): Current rolling mean
        new_value: float: New value to incorporate
        count: int: Number of reviews considered so far

    Returns:
        float: Updated rolling mean
    """
    return ((current_mean * count) + new_value) / (count + 1)

# Function for predicting sentiment scores
def predict_sentiment(review: str) -> np.ndarray:
    """
    Predicts sentiment scores for a given review.

    Args:
        review (str): Review text

    Returns:
        np.ndarray: Array of sentiment scores for each attribute
    """
    # Tokenize the input review
    inputs = tokenizer(review, return_tensors='pt', truncation=True, padding=True, max_length=512)
    
    # Disable gradient calculations for inference
    with torch.no_grad():
        # Get model outputs
        outputs = model(**inputs)
    
    # Get the prediction logits
    predictions = outputs.logits.squeeze().detach().numpy()
    return predictions

# Function to print predictions with labels
def print_predictions(review: str, predictions: np.ndarray):
    """
    Prints the predictions with labels.

    Args:
        review (str): Review text
        predictions (np.ndarray): Predicted sentiment scores
    """
    print(f"Review: {review}")
    for label, score in zip(label_columns, predictions):
        print(f"{label}: {score:.2f}")

# Function to compute the overall rating using weighted mean
def compute_overall_rating(predictions: np.ndarray, weights: Dict[str, float]) -> float:
    """
    Computes the overall rating using weighted mean, ignoring aspects with a value of 5.

    Args:
        predictions (np.ndarray): Predicted sentiment scores
        weights (Dict[str, float]): Weights for each attribute

    Returns:
        float: Overall rating
    """
    filtered_predictions = []
    filtered_weights = []

    for i, pred in enumerate(predictions):
        if pred != 5:  # Ignore aspects with a value of 5
            filtered_predictions.append(pred)
            filtered_weights.append(weights[label_columns[i]])

    if not filtered_predictions:  # All aspects have a value of 5
        return 5.0

    weighted_sum = sum(pred * weight for pred, weight in zip(filtered_predictions, filtered_weights))
    total_weight = sum(filtered_weights)
    return weighted_sum / total_weight

# Function to calculate normal mean for initial reviews
def get_rating(reviews: List[str], entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Returns the Probabilities of the Attributes in the Text

    Args:
        reviews: List of review texts
        entity: Name of the entity
        attributes: List of Attributes to rate
        entity_data: all entities, their aspects and their weights

    Return:
        Dict: Probabilities of the Attributes {"attribute_1":0.3,"attribute_2":0.7} i.e Aspect-wise weighted mean.
        LM6: Final Rating
    """
    try:
        # Initialize list to store sentiment scores for each attribute
        all_scores = {attribute: [] for attribute in attributes}

        for review in reviews:
            # Split review into sentences
            sentences = sent_tokenize(review)
            for sentence in sentences:
                sentiment_scores = predict_sentiment(sentence)
                for i, attribute in enumerate(attributes):
                    # removing neutral values (not talked about topics shouldn't affect the mean value)
                    if abs(sentiment_scores[i]) > 0.2:
                        all_scores[attribute].append(sentiment_scores[i])

        # Calculate the mean score for each attribute
        probabilities = {attribute: np.mean(scores) if scores else 0.0 for attribute, scores in all_scores.items()}

        # Compute overall rating using the weighted mean
        overall_rating = compute_overall_rating(
            np.array([probabilities[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        probabilities['LM6'] = overall_rating

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}

# Function to update ratings with a new review using rolling mean
def update_rating_with_new_review(review: str, current_ratings: Dict[str, float], count: int, entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Updates the ratings with a new review using the rolling mean.

    Args:
        review: str: New review text
        current_ratings: Dict[str, float]: Current ratings for each attribute
        count: int: Number of reviews considered so far
        entity: str: Name of the entity
        attributes: List[str]: List of Attributes to rate
        entity_data: Dict: All entities, their aspects and their weights

    Return:
        Dict: Updated ratings for each attribute
    """
    try:
        # Split review into sentences
        sentences = sent_tokenize(review)
        for sentence in sentences:
            sentiment_scores = predict_sentiment(sentence)
            for i, attribute in enumerate(attributes):
                if abs(sentiment_scores[i]) > 0.2:
                    current_ratings[attribute] = rolling_mean_update(current_ratings[attribute], sentiment_scores[i], count)

        # Update overall rating using the weighted mean
        overall_rating = compute_overall_rating(
            np.array([current_ratings[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        current_ratings['LM6'] = overall_rating

        return current_ratings

    except Exception as e:
        print(f"Error in updating ratings: {e}")
        return current_ratings
