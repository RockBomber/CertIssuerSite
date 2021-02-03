#!/usr/bin/env bash

gunicorn server:app --bind localhost:5000 --worker-class aiohttp.GunicornWebWorker
