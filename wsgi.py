"""WSGI entry point for gunicorn."""

from app import app

application = app
