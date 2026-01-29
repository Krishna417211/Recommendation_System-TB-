import os
import pandas as pd
import json
import ast
import numpy as np
from django.core.management.base import BaseCommand
from core.models import Movie
from django.conf import settings

class Command(BaseCommand):
    help = 'Import all 45k movies from movies_metadata.csv'

    def handle(self, *args, **kwargs):
        # Path to data
        base_dir = settings.BASE_DIR
        project_root = base_dir.parent 
        movies_csv = os.path.join(project_root, 'data', 'movies_metadata.csv')

        self.stdout.write(f"Looking for data at: {movies_csv}")

        if not os.path.exists(movies_csv):
            self.stdout.write(self.style.ERROR('Movies CSV not found!'))
            return

        # Load Data
        self.stdout.write("Loading CSV...")
        movies = pd.read_csv(movies_csv, low_memory=False)
        
        # Clean Data (Logic from generate_models.py)
        # Drop rows with bad IDs
        movies['id'] = pd.to_numeric(movies['id'], errors='coerce')
        movies = movies.dropna(subset=['id'])
        movies['id'] = movies['id'].astype(int)
        
        # Drop rows with no release date (optional, but good for quality)
        movies = movies[movies['release_date'].notna()]

        self.stdout.write(f"Found {len(movies)} valid movies. Starting import...")

        # Helper to parse fields
        def parse_json_field(text):
            try:
                return json.loads(text.replace("'", '"')) # Try simple replace
            except:
                try:
                    return ast.literal_eval(text)
                except:
                    return []

        count = 0
        created_count = 0
        
        # Bulk create optimization could be used, but let's stick to safe iterative for now to handle data errors
        # To speed up, we can use transaction.atomic()
        from django.db import transaction

        # Get existing IDs to avoid duplicates efficiently
        existing_ids = set(Movie.objects.values_list('tmdb_id', flat=True))
        
        batch_size = 1000
        batch = []
        
        for index, row in movies.iterrows():
            tmdb_id = row['id']
            
            if tmdb_id in existing_ids:
                continue

            try:
                # Parse Genres
                raw_genres = parse_json_field(row['genres'])
                genre_names = [g['name'] for g in raw_genres if isinstance(g, dict) and 'name' in g]
                
                # Parse Keywords (optional, stored if needed)
                # raw_keywords = parse_json_field(row['keywords'])
                # keyword_names = [k['name'] for k in raw_keywords]

                movie = Movie(
                    title=str(row['title']),
                    overview=str(row['overview']) if pd.notna(row['overview']) else '',
                    tmdb_id=tmdb_id,
                    popularity=float(row['popularity']) if pd.notna(row['popularity']) else 0.0,
                    vote_average=float(row['vote_average']) if pd.notna(row['vote_average']) else 0.0,
                    vote_count=int(row['vote_count']) if pd.notna(row['vote_count']) else 0,
                    genres=json.dumps(genre_names),
                    # keywords=json.dumps(keyword_names), # Model has this field? Yes.
                    release_date=row['release_date'] if pd.notna(row['release_date']) else None
                )
                
                # Handling Poster Path (not in metadata csv usually, unless joined)
                # movies_metadata.csv has 'poster_path'
                if pd.notna(row.get('poster_path')):
                    movie.poster_path = row['poster_path']

                batch.append(movie)
                existing_ids.add(tmdb_id)
                count += 1
                
                if len(batch) >= batch_size:
                    with transaction.atomic():
                        Movie.objects.bulk_create(batch)
                    created_count += len(batch)
                    self.stdout.write(f"Imported {created_count} movies...")
                    batch = []

            except Exception as e:
                # self.stdout.write(self.style.WARNING(f"Error preparing row {index}: {e}"))
                continue
        
        # Final batch
        if batch:
            with transaction.atomic():
                Movie.objects.bulk_create(batch)
            created_count += len(batch)

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {created_count} new movies! (Total processed: {count})'))
