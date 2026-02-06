#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r movie_recommender/requirements.txt

cd movie_recommender
python manage.py collectstatic --no-input
python manage.py migrate
