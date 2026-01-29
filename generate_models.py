import pandas as pd
import numpy as np
import ast
import pickle
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = BASE_DIR # Save to root as per utils.py expectation

def load_data():
    print("Loading datasets...")
    movies = pd.read_csv(os.path.join(DATA_DIR, 'movies_metadata.csv'), low_memory=False)
    credits = pd.read_csv(os.path.join(DATA_DIR, 'credits.csv'))
    keywords = pd.read_csv(os.path.join(DATA_DIR, 'keywords.csv'))
    
    # Filter bad data (movies with valid dates and votes usually implies valid entries)
    # The 45k dataset has some bad rows
    movies = movies[movies['release_date'].notna()]
    
    # Convert ID to numeric and handle errors
    movies['id'] = pd.to_numeric(movies['id'], errors='coerce')
    movies = movies.dropna(subset=['id'])
    movies['id'] = movies['id'].astype(int)
    
    credits['id'] = credits['id'].astype(int)
    keywords['id'] = keywords['id'].astype(int)
    
    # Merge
    print("Merging datasets...")
    movies = movies.merge(credits, on='id')
    movies = movies.merge(keywords, on='id')
    
    return movies

def convert(obj):
    try:
        L = []
        for i in ast.literal_eval(obj):
            L.append(i['name'])
        return L
    except:
        return []

def convert3(obj):
    try:
        L = []
        counter = 0
        for i in ast.literal_eval(obj):
            if counter != 3:
                L.append(i['name'])
                counter += 1
            else:
                break
        return L
    except:
        return []

def fetch_director(obj):
    try:
        L = []
        for i in ast.literal_eval(obj):
            if i['job'] == 'Director':
                L.append(i['name'])
                break
        return L
    except:
        return []

def preprocess_data(movies):
    print("Preprocessing data...")
    # Select important columns
    # 'id' is TMDB ID
    movies = movies[['id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'popularity', 'release_date', 'vote_average', 'vote_count']]
    
    # Handle missing values
    movies.dropna(inplace=True)
    
    # Extract tags
    movies['genres'] = movies['genres'].apply(convert)
    movies['keywords'] = movies['keywords'].apply(convert)
    movies['cast'] = movies['cast'].apply(convert3)
    movies['crew'] = movies['crew'].apply(fetch_director)
    movies['overview'] = movies['overview'].apply(lambda x: x.split())
    
    # Clean spaces
    def collapse(L):
        L1 = []
        for i in L:
            L1.append(i.replace(" ",""))
        return L1
    
    movies['genres'] = movies['genres'].apply(collapse)
    movies['keywords'] = movies['keywords'].apply(collapse)
    movies['cast'] = movies['cast'].apply(collapse)
    movies['crew'] = movies['crew'].apply(collapse)
    
    # Create tags column
    movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']
    
    # Final dataframe
    new_df = movies[['id', 'title', 'tags', 'popularity', 'release_date', 'vote_average', 'vote_count']].copy()
    new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
    new_df['tags'] = new_df['tags'].apply(lambda x: x.lower())
    
    # Rename id to movie_id for consistency with some parts of app, but 'id' is standard TMDB
    new_df.rename(columns={'id': 'movie_id'}, inplace=True)
    
    # CRITICAL: Reset index so that df index matches array position (0..N-1)
    new_df.reset_index(drop=True, inplace=True)
    
    return new_df

def stem_text(text):
    ps = PorterStemmer()
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

def generate_similarity(new_df):
    print("Stemming tags...")
    new_df['tags'] = new_df['tags'].apply(stem_text)
    
    print("Vectorizing...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(new_df['tags']) # Keep sparse for speed
    
    # Optimization: To avoid MemoryError with 45k x 45k float matrix (16GB+ RAM)
    # We will compute cosine similarity in chunks and ONLY store the top 20 indices
    
    n_movies = vectors.shape[0]
    # We store indices of top similar movies. 20 should be enough for recommendations.
    # Using int32 to save space.
    top_k = 20
    similarity_indices = np.zeros((n_movies, top_k), dtype=np.int32)
    
    print(f"Calculating similarity for {n_movies} movies (Chunked)...")
    
    chunk_size = 1000 
    for i in range(0, n_movies, chunk_size):
        end = min(i + chunk_size, n_movies)
        
        # Compute similarity for this chunk against ALL movies
        # vectors[i:end] shape: (chunk_size, 5000)
        # vectors shape: (n_movies, 5000)
        # Result shape: (chunk_size, n_movies)
        # This will still use some RAM but much less than full matrix
        # (1000 * 45000 * 8 bytes ≈ 360MB) - perfectly safe
        
        sim_chunk = cosine_similarity(vectors[i:end], vectors)
        
        # For each row in chunk, find top K
        # argsort gives indices of sorted elements (ascending)
        # we take last k (highest scores) and reverse to get descending
        
        for idx_in_chunk, row_sim in enumerate(sim_chunk):
            real_idx = i + idx_in_chunk
            # Get indices of top K highest values
            # argpartition is faster than sort for just getting top k
            top_indices = np.argpartition(row_sim, -top_k)[-top_k:]
            
            # Sort these top K so highest is first
            top_scores = row_sim[top_indices]
            sorted_top_indices = top_indices[np.argsort(top_scores)[::-1]]
            
            similarity_indices[real_idx] = sorted_top_indices
            
        print(f"Processed {end}/{n_movies}")

    return similarity_indices

def main():
    movies = load_data()
    print(f"Loaded {len(movies)} movies.")
    
    new_df = preprocess_data(movies)
    
    similarity = generate_similarity(new_df)
    
    print("Saving models...")
    pickle.dump(new_df, open(os.path.join(OUTPUT_DIR, 'movies.pkl'), 'wb'))
    pickle.dump(similarity, open(os.path.join(OUTPUT_DIR, 'similarity.pkl'), 'wb'))
    
    print("Done! Files saved to:")
    print(os.path.join(OUTPUT_DIR, 'movies.pkl'))
    print(os.path.join(OUTPUT_DIR, 'similarity.pkl'))

if __name__ == '__main__':
    main()
