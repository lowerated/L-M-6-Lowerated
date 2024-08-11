import torch
from transformers import BertTokenizer, BertForTokenClassification, pipeline
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Dict, List
from tqdm import tqdm

# Load models and tokenizer
aspect_model = BertForTokenClassification.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')
aspect_tokenizer = BertTokenizer.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')
sentiment_classifier = pipeline("zero-shot-classification", model="Lowerated/lm6-deberta-v3-topic-sentiment")

# Define the label mapping
label_columns = ['Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions']

def get_weights(entity: str, entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Retrieve the weights for each attribute of the given entity.

    Args:
        entity (str): The name of the entity (e.g., 'Movie').
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: A dictionary of attribute weights for the entity.
    """
    return entity_data.get(entity, {}).get('weights', {label: 1 for label in label_columns})

def rolling_mean_update(current_mean: float, new_value: float, count: int) -> float:
    """
    Description:
        Update the rolling mean with a new value, considering a threshold to ignore small changes.

    Args:
        current_mean (float): The current mean value.
        new_value (float): The new value to incorporate into the rolling mean.
        count (int): The number of data points considered so far.
        threshold (float): The minimum change required to update the mean.

    Return:
        float: The updated rolling mean.
    """
    if abs(new_value - current_mean) == 0:
        return current_mean
    return ((current_mean * count) + new_value) / (count + 1)

def predict_snippet(review: str, aspect: str) -> List[str]:
    """
    Description:
        Predict and extract snippets from a review that are relevant to a specific aspect.

    Args:
        review (str): The text of the review.
        aspect (str): The aspect (e.g., 'Story', 'Cinematography') for which snippets are being extracted.

    Return:
        List[str]: A list of snippets relevant to the aspect.
    """
    model = aspect_model
    tokenizer = aspect_tokenizer
    model.eval()

    inputs = tokenizer.encode_plus(
        review,
        aspect,
        add_special_tokens=False,
        max_length=256,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation='longest_first'
    )
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    predictions = torch.argmax(logits, dim=2).flatten().tolist()
    new_predictions = predictions.copy()
    tokens = tokenizer.convert_ids_to_tokens(input_ids.flatten().tolist())
    
    snippets = []
    snippet = []
    i = 0
    for token, label in zip(tokens, predictions):
        if label == 1:
            new_predictions[i] = 1
            snippet.append(token)
        elif label == 0 and i > 0 and i + 1 < len(tokens) and predictions[i - 1] == 1 and predictions[i + 1] == 1:
            new_predictions[i] = 1
            snippet.append(token)
        elif len(snippet):
            snippets.append(' '.join(snippet))
            snippet = []
        i += 1

    for i in range(1, len(new_predictions) - 2):
        if new_predictions[i] == 0 and new_predictions[i+1] == 0 and new_predictions[i-1] == 1 and new_predictions[i+2] == 1:
            new_predictions[i] = 1
            new_predictions[i+1] = 1

    return snippets

def get_sentiment_score(snippet: str, aspect: str) -> float:
    """
    Description:
        Determine the sentiment score of a snippet for a specific aspect.

    Args:
        snippet (str): The text snippet related to an aspect.
        aspect (str): The aspect being analyzed.

    Return:
        float: The sentiment score scaled between 0 and 10.
    """
    positive_label = f"{aspect} positive"
    negative_label = f"{aspect} negative"
    sentiment_result = sentiment_classifier(snippet, [positive_label, negative_label])
    positive_score = sentiment_result['scores'][0]
    negative_score = sentiment_result['scores'][1]
    scaled_score = ((positive_score - negative_score + 1) / 2) * 10  # Already scaled to 0-10

    return scaled_score

def compute_overall_rating(predictions: np.ndarray, weights: Dict[str, float]) -> float:
    """
    Description:
        Compute the overall rating for an entity by applying weights to the aspect predictions.

    Args:
        predictions (np.ndarray): Array of sentiment scores for each aspect.
        weights (Dict[str, float]): A dictionary of weights for each aspect.

    Return:
        float: The overall weighted rating.
    """
    filtered_predictions = []
    filtered_weights = []

    for i, pred in enumerate(predictions):
        if pred != 0:
            filtered_predictions.append(pred)
            filtered_weights.append(weights[label_columns[i]])

    if not filtered_predictions:
        return 0.0

    weighted_sum = sum(pred * weight for pred, weight in zip(filtered_predictions, filtered_weights))
    total_weight = sum(filtered_weights)
    return weighted_sum / total_weight

def get_rating(reviews: List[str], entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Calculate the sentiment ratings for a list of reviews and compute an overall rating.

    Args:
        reviews (List[str]): A list of review texts.
        entity (str): The name of the entity (e.g., 'Movie').
        attributes (List[str]): A list of attributes/aspects to rate.
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: A dictionary of sentiment scores for each aspect, including the overall 'LM6' rating.
    """
    try:
        all_scores = {attribute: [] for attribute in attributes}

        for review in tqdm(reviews):
            # Split review into sentences
            sentences = sent_tokenize(review)
            for sentence in sentences:
                for aspect in attributes:
                    snippets = predict_snippet(sentence, aspect)
                    for snippet in snippets:
                        score = get_sentiment_score(snippet, aspect)
                        all_scores[aspect].append(score)

        probabilities = {attribute: np.mean(scores) if scores else 0.0 for attribute, scores in all_scores.items()}

        overall_rating = compute_overall_rating(
            np.array([probabilities[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        probabilities['LM6'] = overall_rating

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}

def update_rating_with_new_review(review: str, current_ratings: Dict[str, float], count: int, entity: str, attributes: List[str], entity_data: Dict) -> Dict[str, float]:
    """
    Description:
        Update the current sentiment ratings with a new review. If the previous value for an aspect is zero,
        it calculates a normal mean instead of using a rolling mean.

    Args:
        review (str): The new review text.
        current_ratings (Dict[str, float]): The current ratings for each attribute.
        count (int): The number of reviews considered so far.
        entity (str): The name of the entity (e.g., 'Movie').
        attributes (List[str]): A list of attributes/aspects to rate.
        entity_data (Dict): A dictionary containing entity information and their respective weights.

    Return:
        Dict[str, float]: The updated ratings for each attribute, including the overall 'LM6' rating.
    """
    try:
        sentences = sent_tokenize(review)
        for sentence in sentences:
            for aspect in attributes:
                snippets = predict_snippet(sentence, aspect)
                for snippet in snippets:
                    score = get_sentiment_score(snippet, aspect)
                    if current_ratings[aspect] == 0:
                        # If the previous rating was zero, take the normal mean of the two values
                        current_ratings[aspect] = score
                    else:
                        # Use rolling mean update if the previous rating is not zero
                        current_ratings[aspect] = rolling_mean_update(current_ratings[aspect], score, count)

        overall_rating = compute_overall_rating(
            np.array([current_ratings[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        current_ratings['LM6'] = overall_rating

        return current_ratings

    except Exception as e:
        print(f"Error in updating ratings: {e}")
        return current_ratings
