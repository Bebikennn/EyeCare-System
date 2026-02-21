"""WSGI entrypoint for production servers (gunicorn, uwsgi)."""

from app import app


# Gunicorn looks for a module-level variable named `application` by default in
# some conventions, but we keep `app` as the primary export.
application = app
