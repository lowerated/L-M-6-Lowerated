import json
from typing import List, Dict
from openai import OpenAI


def entities() -> List[str]:
    """
    Returns All the Default Entities Available in the Lowerated Library

    Return:
        List[str]: List of Entities
    """
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        # just the keys from data in a list
        entities = list(data.keys())
        return entities


def find_attributes(entity: str) -> List[str]:
    """
    Returns All the Default Attributes Available in the Lowerated Library

    Args:
        entity (str): Entity Name
    Return:
        List[str]: List of Attributes
    """
    # read entities.json, send keys
    with open('./lowerated/rate/entities.json', 'r') as file:
        data = json.load(file)
        attributes = data.get(entity, None)
        return attributes


def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """
    Splits text into chunks of specified size.

    Args:
        text: The text to be chunked.
        chunk_size: The maximum size of each chunk.

    Return:
        List of text chunks.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def get_probabilities(reviews: List[str], entity: str, attributes: List[str], key: str = None) -> Dict:
    """
    Returns the Probabilities of the Attributes in the Text

    Args:
        reviews: List of review texts
        entity: Name of the entity
        attributes: List of Attributes to rate
        key: OpenAI API key

    Return:
        Dict: Probabilities of the Attributes {"attribute_1":0.3,"attribute_2":0.7}
    """

    if key is None:
        raise ValueError("OpenAI API key is required")

    # Set the OpenAI API key
    client = OpenAI()

    # Join all reviews into a single string for context
    reviews_text = "\n".join(reviews)

    # Prepare the prompt template
    prompt_template = f"""Analyze the following reviews for the entity '{entity}' and provide probabilities for the following attributes as a JSON object with values ranging from -1 to 1: {', '.join(attributes)}.

    -1 means, sentiment of that attibute is negative
    1 means, sentiment of that attibute is positive
    0 means an attribute isn't talked about or the sentiment is neutral.

    YOU must give me response like this:
    {{"attribute_1":-0.3, "attribute_2":0.7}}

    Reviews: """

    try:
        probabilities = {attribute: 0.0 for attribute in attributes}

        # Split reviews into chunks if necessary
        review_chunks = chunk_text(text=reviews_text, chunk_size=4000)

        for chunk in review_chunks:
            prompt = prompt_template + chunk

            # Call the OpenAI GPT-3.5-turbo model
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )

            # Extract the generated text from the response
            generated_text = response.choices[0].message.content

            # print("generated text: ", generated_text)

            # Parse the generated text as JSON
            chunk_probabilities = json.loads(generated_text)

            # Aggregate probabilities
            for attribute in attributes:
                if attribute in chunk_probabilities:
                    probabilities[attribute] += chunk_probabilities[attribute]

        # Average probabilities over the number of chunks
        for attribute in probabilities:
            probabilities[attribute] /= len(review_chunks)

        return probabilities

    except Exception as e:
        print(f"Error in getting probabilities: {e}")
        return {}


def calculate_cost(reviews: List[str] = None, model: str = "gpt-3.5-turbo-0125") -> float:
    """
        Calculate how much it would cost to get the rating from reviews.
    """

    # Define the pricing per model
    pricing = {
        "gpt-3.5-turbo-0125": {
            "input_cost_per_million": 0.50,
            "output_cost_per_million": 1.50
        }
    }

    # Get the pricing for the specified model
    if model not in pricing:
        raise ValueError(
            "Model not recognized. Please use a valid model name.")

    input_cost_per_million = pricing[model]["input_cost_per_million"]
    output_cost_per_million = pricing[model]["output_cost_per_million"]

    # Convert the list of reviews to a single string
    if isinstance(reviews, list):
        text = " ".join(reviews)
    else:
        raise ValueError("Input must be a list of reviews.")

        # Calculate the number of input tokens in the text
    # Here, we assume 1 token is roughly 4 characters
    num_input_tokens = len(text) / 4  # This is a rough estimation

    # The number of output tokens is fixed (200 characters / 4 characters per token)
    num_output_tokens = 200 / 4

    # Calculate the cost for input and output tokens
    input_cost = (num_input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (num_output_tokens / 1_000_000) * output_cost_per_million

    # Total cost is the sum of input and output costs
    total_cost = input_cost + output_cost

    return total_cost
