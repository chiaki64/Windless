#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from components.eternity import config
from task.celery import app


@app.task
def restart(x):
    config.eternity['env']['flag'] = not config.eternity['env']['flag']
    config.dumps(config.eternity)
    return x

@app.task
def add(x, y):
    return x+y
