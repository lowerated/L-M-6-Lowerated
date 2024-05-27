# Lowerated's Rating Algorithm

![Logo](./media/logos/main-logo-black-background.jpeg)

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

We have identified key attributes for multiple entities, detailed in the listed in [entities & attributes](./docs/rate/entities_attributes.md)


## Can we add more attributes?
Yes, 7 is the standard for all the default entities given, you can create your own entities and assign them as many attributes you want.

## How do I use it?
Check Out the steps to use Lowerated [here](./docs/rate/how_to_use.md)

### Lisence
[Apache 2.0](./LICENSE)
 
Copyright (2024) FACT-RATED MEDIA (PVT-LTD)
