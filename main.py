from lowerated.rate.entity import Entity

# Example usage
if __name__ == "__main__":
    some_movie_reviews = [
        "bad movie!", "worse than other movies.", "bad.",
        "best movie", "very good movie", "the cinematography was insane",
        "story was so beautiful", "the emotional element was missing but cinematography was great",
        "didn't feel a thing watching this",
        "oooof, eliot and jessie were so good. the casting was the best",
        "yo who designed the set, that was really good",
        "such stories are rare to find"
    ]

    # Create entity object (loads the whole pipeline)
    # list of aspects. ('Cinematography', 'Direction', 'Story', 'Characters', 'Production Design', 'Unique Concept', 'Emotions')
    entity = Entity(name="Movie")

    rating = entity.rate(reviews=some_movie_reviews)

    print("LM6: ", rating["LM6"])
