from lowerated.rate.entity import Entity

# Example usage
if __name__ == "__main__":
    initial_reviews = [
        "the story was breathtakingly amazing."
    ]
    
    new_review = "The story was amazing, but the cinematography could not have been better."

    # Create entity object (loads the whole pipeline)
    entity = Entity(name="Movie")

    # Calculate initial ratings
    initial_rating = entity.rate(reviews=initial_reviews)
    print("Initial Rating:", initial_rating)
    print("Initial LM6:", initial_rating["LM6"])

    # Update the rating with a new review
    updated_rating = entity.update_rating(
        new_review=new_review,
        current_ratings=initial_rating,
        count=len(initial_reviews)
    )
    
    print("Updated Rating:", updated_rating)
    print("Updated LM6:", updated_rating["LM6"])
