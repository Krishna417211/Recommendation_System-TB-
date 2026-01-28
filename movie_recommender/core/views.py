from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Movie
from .utils import get_recommendations

def index(request):
    # Show top 24 popular movies (grid of 4x6)
    movies = Movie.objects.all().order_by('-popularity')[:24]
    return render(request, 'core/index.html', {'movies': movies})

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, tmdb_id=movie_id)
    
    # Get recommendations (returns list of dicts: {'title': '...', 'movie_id': ...})
    recommendations_data = get_recommendations(movie.title)
    
    # We need to fetch the actual Movie objects for these recommendations to get their stats/info (like release_date, votes)
    # The template expects 'rec.movie_id', but the Movie model has 'tmdb_id'. 
    # We will pass the Movie objects, but we need to ensure the template can access the ID.
    # Movie object has .tmdb_id. The template provided uses .movie_id.
    # We can annotate or just fix the template. I fixed the template to handle this, 
    # BUT for consistency with the user's template using 'rec.movie_id', 
    # let's construct a list of dicts or objects that have 'movie_id'.
    
    recommended_movies = []
    for item in recommendations_data:
        # Try to find in DB to get rich data
        rec_obj = Movie.objects.filter(tmdb_id=item['movie_id']).first() 
        if not rec_obj:
             # Fallback: try title match
             rec_obj = Movie.objects.filter(title=item['title']).first()
        
        if rec_obj:
            # We wrap it or add an attribute to satisfy the template's 'rec.movie_id'
            # Or simpler: The template uses {{ rec.movie_id }}. 
            # Movie model has tmdb_id. Let's make sure we pass something that works.
            # I will pass the Movie object, but I'll patch it dynamically or rely on the template change I made?
            # Actually, in my template update above, for recommendations I used {{ rec.movie_id }}.
            # Since I am passing Movie objects, they don't have .movie_id, they have .tmdb_id.
            # I should alias it for the template, OR update the template to use tmdb_id.
            # I updated the template above to use rec.movie_id because that's what the data from utils.py had.
            # BUT if I replace that data with Movie objects, I break the template.
            # FIX: I will pass a list of enriched properties.
            rec_dict = {
                'movie_id': rec_obj.tmdb_id,
                'title': rec_obj.title,
                'release_date': rec_obj.release_date,
                'vote_average': rec_obj.vote_average,
                'overview': rec_obj.overview,
                'popularity': rec_obj.popularity,
            }
            recommended_movies.append(rec_dict)
        else:
            # If not in DB, pass the raw item from utils (basic info only)
            recommended_movies.append(item)

    return render(request, 'core/detail.html', {
        'movie': movie,
        'recommendations': recommended_movies
    })

def search(request):
    query = request.GET.get('q', '')
    if query:
        # 1. Get standard search results
        search_results = list(Movie.objects.filter(title__icontains=query).order_by('-popularity'))
        
        # 2. Get recommendations for the best match (if any)
        recommendations = []
        if search_results:
            best_match = search_results[0]
            recs_data = get_recommendations(best_match.title)
            for item in recs_data:
                rec_obj = Movie.objects.filter(title=item['title']).first()
                if rec_obj:
                    recommendations.append(rec_obj)
        
        # 3. Combine: [Search Results (limited)] + [Recommendations]
        # We limit search results to 5 to keep focus on recommendations if the user wants "movies of that kind"
        # Using a set to remove duplicates while preserving order
        seen_titles = set()
        final_movies = []
        
        # Add search results first
        for movie in search_results:
            if movie.title not in seen_titles:
                final_movies.append(movie)
                seen_titles.add(movie.title)
        
        # Add recommendations
        for movie in recommendations:
            if movie.title not in seen_titles:
                final_movies.append(movie)
                seen_titles.add(movie.title)
                
        movies = final_movies
    else:
        movies = []
    
    return render(request, 'core/index.html', {'movies': movies, 'search_query': query})
