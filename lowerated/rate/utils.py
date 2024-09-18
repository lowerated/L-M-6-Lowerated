import torch
from transformers import BertTokenizer, BertForTokenClassification, pipeline
import numpy as np
from nltk.tokenize import sent_tokenize
from typing import Dict, List
from tqdm import tqdm
import re

# Load models and tokenizer
aspect_model = BertForTokenClassification.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')
aspect_tokenizer = BertTokenizer.from_pretrained('Lowerated/lm6-movie-aspect-extraction-bert')

# Check if GPU is available and set device accordingly
device = 0 if torch.cuda.is_available() else -1  # device=0 for GPU, device=-1 for CPU

# Move the aspect model to GPU if available
aspect_model.to('cuda' if device == 0 else 'cpu')

# Initialize the sentiment classifier pipeline with the correct device
sentiment_classifier = pipeline("zero-shot-classification", model="Lowerated/lm6-deberta-v3-topic-sentiment", device=device)

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
        Update the rolling mean with a new value.

    Args:
        current_mean (float): The current mean value.
        new_value (float): The new value to incorporate into the rolling mean.
        count (int): The number of data points considered so far.

    Return:
        float: The updated rolling mean.
    """
    if abs(new_value - current_mean) == 0:
        return current_mean
    updated_mean = ((current_mean * count) + new_value) / (count + 1)
    # Ensure the updated mean does not exceed 10
    return max(0, min(10, updated_mean))


def remove_specific_characters(strings_list):
    # Define the characters to be removed
    characters_to_remove = {
    '\x8d', '\x8b', '\x8c', '\x8f', '\x87', '\x8e', '\x81',
    '\x8a', '\x83', '\x94', '\x95', '\x97', '\x91', '\x89',
    '\x80', '\x99', '\x9e', '\xad', '\x9d', '\x98', '\x93',
    '\x82', '\x9c', '\x9f'"®", "´", "¿", "¥",
        "\u00c3", "\u00a2", "\u00c2", "\u0080", "\u00c2", "\u0099"
    }

    cleaned_strings_list = []

    for string in strings_list:
        cleaned_string = ''.join(char for char in string if char not in characters_to_remove)
        cleaned_strings_list.append(cleaned_string)

    return cleaned_strings_list

def remove_double_spaces(strings):
    pattern = re.compile(r'\s{2,}')  # Regex to match two or more spaces
    return [pattern.sub(' ', text) for text in strings]

def remove_multiple_punctuation(strings):
    # Create patterns to find multiple occurrences of ., !, and ,
    patterns = {
        r'\.{2,}': '.',
        r'\!{2,}': '!',
        r'\,{2,}': ','
    }

    # Process each string in the list
    cleaned_strings = []
    for text in strings:
        for pattern, replacement in patterns.items():
            text = re.sub(pattern, replacement, text)
        cleaned_strings.append(text)

    return cleaned_strings

def clean_text(text):
    original_review= remove_double_spaces([text])
    original_review= remove_multiple_punctuation(original_review)
    original_review = remove_specific_characters(original_review)[0]
    text = original_review.lower()
    text = re.sub(r'\n+', ' ', text)  # Replace newlines with a space
    text = re.sub(r'\.\.+', '.', text)  # Replace multiple periods with a single period
    # text=text.replace(',','')
    # text=text.replace('.','')
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple spaces with a single space
    return text

def fix_special_characters(snippet):
    snippet=snippet.replace("[UNK]",'')
    snippet=snippet.replace(" ##",'')
    snippet=snippet.replace(" '","'")
    snippet=snippet.replace(" ’","’")
    snippet=snippet.replace("’ ","’")
    snippet=snippet.replace("' ","'")
    snippet=snippet.replace(" -","-")
    snippet=snippet.replace("- ","-")
    snippet=snippet.replace("/ ","/")
    snippet=snippet.replace(" /","/")
    snippet=snippet.replace(" :",":")
    snippet=snippet.replace(": ",":")
    return snippet

def predict_snippet(review, aspect, model, tokenizer, max_len=512):
    model.eval()

    # Tokenize the input and move tensors to the correct device
    inputs = tokenizer.encode_plus(
        review,
        aspect,
        add_special_tokens=True,
        max_length=max_len,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
        truncation='longest_first'
    )

    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    # Move model to the correct device
    model.to(device)

    # Make predictions
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits

    # Move logits back to CPU for processing
    predictions = torch.argmax(logits, dim=2).flatten().cpu().tolist()
    new_predictions = predictions.copy()

    # Decode the tokens
    tokens = tokenizer.convert_ids_to_tokens(input_ids.flatten().cpu().tolist())
    snippets = []
    snippet = []
    i = 0

    # Process tokens and labels to extract relevant snippets
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

    # Refine predictions based on the 1,0,0,1 pattern
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

    # Ensure the sentiment score does not exceed 10
    return max(0, min(10, scaled_score))

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
    return max(0, min(10, weighted_sum / total_weight))  # Clamp the overall rating between 0 and 10

def merge_small_snippets(snippets):
    """
    Description:
        Merge small snippets that are less than 5 words long.
    """
    merged_snippets = []
    snippet = ""
    for i in range(len(snippets)):
        if len(snippet.split()) < 5:
            snippet += snippets[i]
        else:
            merged_snippets.append(snippet)
            snippet = snippets[i]
    if snippet:
        merged_snippets.append(snippet)
    return merged_snippets

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
            review = clean_text(review)
            sentences = sent_tokenize(review)
            for sentence in sentences:
                for aspect in attributes:
                    snippets = predict_snippet(sentence, aspect, model=aspect_model, tokenizer=aspect_tokenizer)
                    snippets = merge_small_snippets(snippets)
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
        review = clean_text(review)
        sentences = sent_tokenize(review)
        for sentence in sentences:
            for aspect in attributes:
                snippets = predict_snippet(sentence, aspect, model=aspect_model, tokenizer=aspect_tokenizer)

                # if snippets are small length less than 5, merge them
                snippets = merge_small_snippets(snippets)
                
                for snippet in snippets:
                    score = get_sentiment_score(snippet, aspect)
                    if current_ratings[aspect] == 0:
                        # If the previous rating was zero, take the new score directly
                        current_ratings[aspect] = score
                    else:
                        # Use rolling mean update if the previous rating is not zero
                        current_ratings[aspect] = rolling_mean_update(current_ratings[aspect], score, count)
                    
                    # Ensure the updated rating does not exceed 10
                    current_ratings[aspect] = max(0, min(10, current_ratings[aspect]))

        overall_rating = compute_overall_rating(
            np.array([current_ratings[attr] for attr in attributes]), 
            get_weights(entity, entity_data)
        )
        current_ratings['LM6'] = overall_rating

        return current_ratings

    except Exception as e:
        print(f"Error in updating ratings: {e}")
        return current_ratings

