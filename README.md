# Movie Recommendation System

## Project Overview
This is a movie recommendation web application built with Django. It uses machine learning models to suggest movies based on content similarity.

## How to Run Locally

### 1. Prerequisites
- Python installed (3.10+ recommended)
- `pip` (Python package manager)

### 2. Setup (First Time Only)
Open your terminal/command prompt in the main project folder and navigate to the code directory:
```bash
cd movie_recommender
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Start the Server
Run the following command to start the local development server:
```bash
python manage.py runserver
```

### 4. Access the App
Open your web browser and go to:
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Deployment
A `Procfile` is included for deployment on platforms like Render or Heroku.
Web command: `web: cd movie_recommender && gunicorn movie_recommender.wsgi`
