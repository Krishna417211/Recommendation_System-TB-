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
        
        movies_path = os.path.join(base_dir, 'movie_list.pkl')
        sim_path = os.path.join(base_dir, 'simlarity.pkl') # Note typo in original file
        
        if not os.path.exists(movies_path) or not os.path.exists(sim_path):
            # Fallback for when files might be in 'articficats' folder?
            # Or if running from different context.
            print(f"Artifacts not found at {movies_path}. Checking artifacts dir...")
            movies_path = os.path.join(base_dir, 'articficats', 'movie_list.pkl')
            sim_path = os.path.join(base_dir, 'articficats', 'simlarity.pkl')
        
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
        # Find index
        movie_indices = _MOVIES_DF[_MOVIES_DF['title'] == title].index
        if len(movie_indices) == 0:
            return []
        
        idx = movie_indices[0]
        
        # Get similarity scores
        distances = sorted(list(enumerate(_SIMILARITY[idx])), reverse=True, key=lambda x: x[1])
        
        # Top 5 (excluding self)
        recommended_movies = []
        for i in distances[1:6]:
            row = _MOVIES_DF.iloc[i[0]]
            recommended_movies.append({
                'title': row['title'],
                'movie_id': row['movie_id'] # TMDB ID
            })
            
        return recommended_movies
    except Exception as e:
        print(f"Error generating recommendations for {title}: {e}")
        return []
