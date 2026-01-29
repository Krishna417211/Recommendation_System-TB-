import os
import pickle
import pandas as pd
from django.conf import settings

# Global cache for artifacts
_MOVIES_DF = None
_SIMILARITY = None

def load_artifacts():
    global _MOVIES_DF, _SIMILARITY
    if _MOVIES_DF is None or _SIMILARITY is None:
        base_dir = settings.BASE_DIR.parent # Recommendation_System root
        
        # Updated filenames
        movies_path = os.path.join(base_dir, 'movies.pkl') # Was movie_list.pkl
        sim_path = os.path.join(base_dir, 'similarity.pkl') # Fixed typo
        
        if not os.path.exists(movies_path) or not os.path.exists(sim_path):
            print(f"Artifacts not found at {movies_path}. Checking artifacts dir...")
            movies_path = os.path.join(base_dir, 'artifacts', 'movies.pkl')
            sim_path = os.path.join(base_dir, 'artifacts', 'similarity.pkl')
        
        try:
            with open(movies_path, 'rb') as f:
                _MOVIES_DF = pickle.load(f)
            with open(sim_path, 'rb') as f:
                _SIMILARITY = pickle.load(f)
            print("Successfully loaded recommendation artifacts.")
        except Exception as e:
            print(f"Error loading artifacts: {e}")
            _MOVIES_DF = pd.DataFrame()
            _SIMILARITY = []

def get_recommendations(title):
    load_artifacts()
    
    if _MOVIES_DF.empty:
        return []

    try:
        # Find index (Case Insensitive)
        matches = _MOVIES_DF[_MOVIES_DF['title'].str.lower() == title.lower()]
        if matches.empty:
            return []
        
        # Use first match
        idx = matches.index[0]
        
        # New Logic: _SIMILARITY[idx] now contains INDICES of top matches, not raw scores.
        # The 0-th element is the movie itself, so we take 1:6
        similar_indices = _SIMILARITY[idx][1:6]
        
        recommended_movies = []
        for i in similar_indices:
            row = _MOVIES_DF.iloc[i]
            recommended_movies.append({
                'title': row['title'],
                'movie_id': row['movie_id'] # Ensure generate_models.py creates this column
            })
            
        return recommended_movies
    except Exception as e:
        print(f"Error generating recommendations for {title}: {e}")
        return []

def search_movies(query, search_type):
    """
    Search for movies by Title, Language, or Genre.
    Returns a list of movie IDs (tmdb_id).
    """
    load_artifacts()
    if _MOVIES_DF.empty:
        return []
    
    query = str(query).lower().strip()
    results = []

    try:
        if search_type == 'title':
            # Simple substring match
            mask = _MOVIES_DF['title'].str.lower().str.contains(query, na=False)
            results = _MOVIES_DF[mask]['movie_id'].tolist()
            
        elif search_type == 'language':
            # Exact match on original_language (e.g., 'en', 'ml')
            mask = _MOVIES_DF['original_language'].astype(str).str.lower() == query
            results = _MOVIES_DF[mask]['movie_id'].tolist()
            
        elif search_type == 'genre':
            # Substring match on tags (since genres are in tags) OR check 'genres' column if we kept it
            # We didn't keep 'genres' column in generate_models.py preprocess_data return
            # But 'tags' includes genres.
            # Ideally generate_models.py should have preserved 'genres' for better filtering.
            # Fallback: Search in tags, though this might be noisy.
            # Better: Search in tags is acceptable for now.
            mask = _MOVIES_DF['tags'].str.contains(query, na=False)
            results = _MOVIES_DF[mask]['movie_id'].tolist()
            
        return results[:50] # Limit to top 50 to avoid overloading DB
    except Exception as e:
        print(f"Error searching movies: {e}")
        return []
