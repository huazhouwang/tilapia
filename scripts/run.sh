#!/bin/bash
gunicorn --reload "tilapia.api.app:create_app()" --workers 1 --threads 5 "$@"
