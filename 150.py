import csv
import json
import sys
csv.field_size_limit(sys.maxsize)
from lowerated.rate.entity import Entity


# CSV DATA READDD
def read_csv(file_path):
    movies = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            movie_id = int(row['id'])
            movies[movie_id] = {
                'name': row['title'],
                'imdb_rating': float(row['imdb_rating']),
            }
    return movies

def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        # list to dict
        reviews_dict = {str(movie["_id"]): movie for movie in data}
    return reviews_dict


# AVG RATING
def calculate_average_rating(reviews):
    if not reviews:
        return None
    ratings = [review['Rating'] for review in reviews if 'Rating' in review]
    return sum(ratings) / len(ratings) if ratings else None

# creating new CSV and writing into it
def write_results_to_csv(results, file_path):
    with open(file_path, 'w', newline='') as file:
        fieldnames = ['ID', 'Name', 'IMDb Rating', 'Audience Rating', 'Critic Rating', 'LM6']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


def process_movies(csv_file, json_file, output_file):
  # loading json
    movies = read_csv(csv_file)
    reviews_data = read_json(json_file)
    
    results = []
    
    for movie_id, movie in movies.items():
        # Fetch the reviews for the current movie ID
        reviews = reviews_data.get(str(movie_id), {})
        audience_reviews = reviews.get('Audience Reviews', [])
        critic_reviews = reviews.get('Critic Reviews', [])
        
        # avg of audience and critics
        audience_rating = calculate_average_rating(audience_reviews)
        critic_rating = calculate_average_rating(critic_reviews)
        
        # combining all of lm6 
        all_reviews = [review['Critic'] for review in audience_reviews + critic_reviews]
        
      
        entity = Entity(name=movie['name'])
        
       # cal initinal using all reviews
        initial_rating = entity.rate(reviews=all_reviews)
        
        print("Initial Rating:", initial_rating)

        result = {
            'ID': movie_id,
            'Name': movie['name'],
            'IMDb Rating': movie['imdb_rating'],
            'Audience Rating': audience_rating if audience_rating is not None else "N/A",
            'Critic Rating': critic_rating if critic_rating is not None else "N/A",
            'LM6': initial_rating['LM6']
        }
        results.append(result)
    
    # write to new CSV
    write_results_to_csv(results, output_file)




if __name__ == "__main__":
    csv_file_path = "imdb_with_lm6_ratings.csv"
    json_file_path = "Lowerated.Cleaned.json"
    output_file_path = "movies_with_lm6_ratings.csv"
    
    process_movies(csv_file=csv_file_path, json_file=json_file_path, output_file=output_file_path)
