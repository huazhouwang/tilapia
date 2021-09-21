#!/bin/bash

 gunicorn --reload "wallet.api.app:create_app()" --workers=1 --threads 5
