#!/usr/bin/env bash

find /code -name "*.pyc" -delete
python -m compileall /code
echo "Start Listening..."
cd /code/core
nohup python listen.py > /dev/null 2>/code/log/server.log