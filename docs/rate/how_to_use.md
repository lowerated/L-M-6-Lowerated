# How to Use Lowerated's Rating Algorithm

1. Install the LR library `pip install lowerated`
2. Print out the list of entities
    ```python
    from lowerated import entities

    print(entities)
    ```
3. Select the entity of your choice and check its attributes.
    ```python
    from lowerated.rate import find_attributes

    print(find_attributes('movie'))
    ```
4. If you want to create your custom entity, you can create it like this
    ```python
    from lowerated.rate import create_entity

    your_entity = create_entity(
        entity='custom_entity', 
        attributes=['attribute1', 'attribute2',         'attribute3']
    )
    ```
5. To generate ratings based on your reviews:
    ```python
    from lowerated.rate import generate_ratings

    reviews = [
        'The movie was visually stunning, but the plot was lacking.',
        'The characters were well-developed, and the story was engaging.'
    ]

    ratings = generate_ratings('movie', reviews)
    print(ratings)
    ```