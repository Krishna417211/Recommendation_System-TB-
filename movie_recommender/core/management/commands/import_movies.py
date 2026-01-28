import os
import pandas as pd
import json
import ast
from django.core.management.base import BaseCommand
from core.models import Movie
from django.conf import settings

class Command(BaseCommand):
    help = 'Import movies from TMDB CSV files'

    def handle(self, *args, **kwargs):
        # Use BASE_DIR from settings which points to the Django project root (where manage.py is)
        # Data is in the parent directory of the Django project
        base_dir = settings.BASE_DIR
        # data folder is in 'Recommendation_System/data', project is in 'Recommendation_System/movie_recommender'
        # So we go up one level from BASE_DIR
        project_root = base_dir.parent 
        
        movies_csv = os.path.join(project_root, 'data', 'tmdb_5000_movies.csv')
        credits_csv = os.path.join(project_root, 'data', 'tmdb_5000_credits.csv')

        self.stdout.write(f"Looking for data at: {movies_csv}")

        if not os.path.exists(movies_csv):
            self.stdout.write(self.style.ERROR('Movies CSV not found!'))
            return

        # Load Data
        movies = pd.read_csv(movies_csv)
        credits = pd.read_csv(credits_csv)

        # Merge (Logic from Notebook)
        # Check if titles match or if we merge on id. Notebook merged on 'title'.
        # But 'id' is safer. Let's see if credits has 'movie_id'.
        # Notebook: movies = movies.merge(credits,on = 'title')
        # Credits csv has 'movie_id', movies csv has 'id'.
        credits.rename(columns={'movie_id': 'id'}, inplace=True)
        movies = movies.merge(credits, on='title')
        
        # We need to handle duplicate columns if any, but 'title' is the key.
        # movies csv has 'id', credits has 'movie_id' (renamed to id).
        # Merging on title might result in id_x and id_y.
        
        self.stdout.write(f"Found {len(movies)} movies. Starting import...")

        count = 0
        for index, row in movies.iterrows():
            try:
                # Safe JSON parsing helper
                def parse_json_field(text):
                    try:
                        return json.loads(text)
                    except:
                        try:
                            return ast.literal_eval(text)
                        except:
                            return []

                # Extract proper ID (handle merge suffixes if they exist)
                # If merged on title, and both had 'id', pandas creates id_x and id_y.
                tmdb_id = row.get('id_x', row.get('id'))
                
                # Check for duplicates
                if Movie.objects.filter(tmdb_id=tmdb_id).exists():
                    continue

                # Parse Genres into a clean list of names
                raw_genres = parse_json_field(row['genres'])
                genre_names = [g['name'] for g in raw_genres]
                
                # Parse Keywords
                raw_keywords = parse_json_field(row['keywords'])
                keyword_names = [k['name'] for k in raw_keywords]

                Movie.objects.create(
                    title=row['title'],
                    overview=row['overview'],
                    tmdb_id=tmdb_id,
                    popularity=row['popularity'],
                    vote_average=row['vote_average'],
                    vote_count=row['vote_count'],
                    genres=json.dumps(genre_names), # Store as simple JSON list ["Action", "Adventure"]
                    keywords=json.dumps(keyword_names),
                    release_date=row['release_date'] if pd.notna(row['release_date']) else None
                )
                count += 1
                if count % 100 == 0:
                    self.stdout.write(f"Imported {count} movies...")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error importing row {index}: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} movies!'))
