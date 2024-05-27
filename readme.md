# Lowerated's Rating Algorithm

### The best way to rate anything.

- An algorithm that provides accurate ratings for any entity.
- Uses diverse sources: reviews, links, documents, and other resources.
- Completely unbiased.
- Combines AI and human evaluation to determine the true rating of an entity.

### What is an Entity?

- Anything that can be rated.
- Examples include films, cars, books, music, furniture, even your partner.

### How Does It Work?

- We have predefined research attributes that, when measured, give a comprehensive understanding of the item. Let's use a movie as an example.

#### Movie Rating Attributes

We evaluate a movie based on seven attributes:
1. **Cinematography** - Visual appeal and camera work.
2. **Direction** - How well the director conveys the story.
3. **Story** - Plot coherence and engagement.
4. **Characters** - Depth and development of characters.
5. **Production Design** - Quality of the sets and overall look.
6. **Unique Concept** - Originality of the idea.
7. **Emotions** - Emotional impact on the audience.

We gather reviews from multiple critics and users. Our AI extracts information from the text inputs and assigns numerical values to each attribute. This process is repeated for all reviews, and we average the results.

Each attribute is given a percentage value from 0-100%, reflecting its presence in the movie.

We have identified key attributes for multiple entities, detailed in the listed in [entities & attributes](./docs/entities_attributes.md)


## Can we add more attributes?
Yes, 7 is the standard for all the default entities given, you can create your own entities and assign them as many attributes you want.

## How do I use it?
1. Install the LR library `pip install lowerated`
2. Print out the list of entities
    ```python
    from lowerated import entities

    print(entities)
    ```
3. Select the entity of your choice and check its attributes.
    ```python
    from lowerated import find_attributes

    print(find_attributes('movie'))
    ```
4. If you want to create your custom entity, you can create it like this
    ```python
    from lowerated import create_entity

    your_entity = create_entity(
        entity='custom_entity', 
        attributes=['attribute1', 'attribute2',         'attribute3']
    )
    ```
5. To generate ratings based on your reviews:
    ```python
    from lowerated import generate_ratings

    reviews = [
        'The movie was visually stunning, but the plot was lacking.',
        'The characters were well-developed, and the story was engaging.'
    ]

    ratings = generate_ratings('movie', reviews)
    print(ratings)
    ```
