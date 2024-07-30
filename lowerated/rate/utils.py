import torch
from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer
import json
from typing import Dict, List
import numpy as np

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
        new_value (float): New value to incorporate
        count (int): Number of reviews considered so far

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
    inputs = tokenizer(review, return_tensors='pt', truncation=True, padding=True)
    
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
    Computes the overall rating using weighted mean.

    Args:
        predictions (np.ndarray): Predicted sentiment scores
        weights (Dict[str, float]): Weights for each attribute

    Returns:
        float: Overall rating
    """
    weighted_sum = sum(predictions[i] * weights[label_columns[i]] for i in range(len(label_columns)))
    total_weight = sum(weights.values())
    return weighted_sum / total_weight

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
        # Initialize probabilities dictionary with 0.0 for each attribute
        probabilities = {attribute: 0.0 for attribute in attributes}
        # Initialize counts for each attribute to keep track of valid values
        counts = {attribute: 0 for attribute in attributes}
        
        for review in reviews:
            sentiment_scores = predict_sentiment(review)
            for i, attribute in enumerate(attributes):

                # removing neutral values (not talked about topics shouldn't effect the mean value)
                if abs(sentiment_scores[i]) > 0.1:
                    probabilities[attribute] = rolling_mean_update(probabilities[attribute], sentiment_scores[i], counts[attribute])
                    counts[attribute] += 1
        
        # Compute overall rating using the weighted mean
        overall_rating = compute_overall_rating(
            np.array([probabilities[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        probabilities['LM6'] = overall_rating
        
        # Ensure that any aspect without a rating is set to 0
        for attribute in attributes:
            if counts[attribute] == 0:
                probabilities[attribute] = 0.0

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}
