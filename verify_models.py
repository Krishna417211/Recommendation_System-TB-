import pickle
import pandas as pd
import os
import sys

def verify():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    movies_path = os.path.join(base_dir, 'movies.pkl')
    sim_path = os.path.join(base_dir, 'similarity.pkl')

    if not os.path.exists(movies_path) or not os.path.exists(sim_path):
        print("Models not found!")
        return

    print("Loading models...")
    movies = pickle.load(open(movies_path, 'rb'))
    similarity = pickle.load(open(sim_path, 'rb'))
    print("Models loaded.")

    def get_recs(title):
        try:
            matches = movies[movies['title'].str.lower() == title.lower()]
            if matches.empty:
                print(f"Movie '{title}' not found.")
                return
            
            idx = matches.index[0]
            found_title = movies.iloc[idx].title
            print(f"Found match: '{found_title}' (Index: {idx})")
            
            # similarity[idx] contains INDICES
            rec_indices = similarity[idx]
            print(f"Raw indices in similarity row: {rec_indices[:10]}")
            
            # Skip first one (itself)
            rec_indices = rec_indices[1:6]
            
            print(f"Recommendations:")
            for i in rec_indices:
                print(f"- {movies.iloc[i].title}")
            print("-" * 30)
            
        except Exception as e:
            print(f"Error: {e}")

    get_recs('The Dark Knight Rises')
    get_recs('Toy Story')
    get_recs('Jumanji')

if __name__ == "__main__":
    verify()
