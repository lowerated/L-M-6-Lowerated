import torch
from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer
import json
from typing import Dict
import numpy as np

# Load the fine-tuned model and tokenizer
model = DebertaV2ForSequenceClassification.from_pretrained('lowerated/deberta-v3-lm6')
tokenizer = DebertaV2Tokenizer.from_pretrained('lowerated/deberta-v3-lm6')

# Ensure the model is in evaluation mode
model.eval()

# Define the label mapping
label_columns = ['Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions']

# Load entity weights
with open('./lowerated/rate/entities.json', 'r') as file:
    entity_data = json.load(file)

def get_weights(entity: str) -> Dict[str, float]:
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

