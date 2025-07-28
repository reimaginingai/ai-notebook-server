#!/bin/bash
# export FLASK_APP=./server/index.py
# pipenv run flask --debug run -h 0.0.0.0
gunicorn --config server/gunicorn_config.py server.index:app