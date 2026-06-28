#!/usr/bin/env bash
# exit on error
set -o errexit

# Packages install karo
pip install -r requirements.txt

# Static files collect karo
python manage.py collectstatic --no-input

# Database migrations run karo
python manage.py migrate