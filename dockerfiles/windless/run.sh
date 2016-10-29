#!/usr/bin/env bash

find /code -name "*.pyc" -delete
python -m compileall /code
echo "Start Listening..."
nohup python /code/core/listen.py > /dev/null 2>server.log