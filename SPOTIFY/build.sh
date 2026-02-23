#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

python manage.py collectstatic --no-input
python manage.py migrate
