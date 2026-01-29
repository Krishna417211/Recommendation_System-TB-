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
    filter_type = request.GET.get('type', 'title') # 'title', 'language', 'genre'
    
    movies = []
    
    if query:
        # Use our updated utils function to find matching IDs
        from .utils import search_movies
        matching_ids = search_movies(query, filter_type)
        
        if matching_ids:
            # Fetch objects from DB preserving order
            # Django's 'in' lookup doesn't preserve order, so we fetch and sort in python
            fetched_movies = Movie.objects.filter(tmdb_id__in=matching_ids)
            movie_map = {m.tmdb_id: m for m in fetched_movies}
            
            for mid in matching_ids:
                if mid in movie_map:
                    movies.append(movie_map[mid])
        
        # If searching by title and we have a "best match", we could append recommendations too
        # But for specific filters like "Language", we should probably just show the results.
        if filter_type == 'title' and movies:
             # Logic to add recommendations for the first result could go here similar to before
             pass

    return render(request, 'core/index.html', {
        'movies': movies, 
        'search_query': query,
        'filter_type': filter_type
    })
