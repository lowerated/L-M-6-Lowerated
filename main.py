from lowerated.rate.entity import Entity

# Example usage
if __name__ == "__main__":
    some_movie_reviews = [
        "good movie!", "best than other movies.", "best.",
        "best movie", "very good movie", "the cinematography was insane",
        "story was so beautiful", "the emotional element was missing but cinematography was great",
        "wow feel a thing watching this",
        "oooof, eliot and jessie were so good. the casting was the best",
        "yo who designed the set, that was really good",
        "such stories are rare to find"
    ]

    # Create entity object (loads the whole pipeline)
    entity = Entity(name="Movie")

    rating = entity.rate(reviews=some_movie_reviews)

    rating = entity.scale_rating(rating)

    print(rating)


    print("LM6: ", rating["LM6"])
