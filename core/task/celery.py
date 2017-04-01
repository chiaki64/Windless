#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from celery import Celery

app = Celery('task', include=['task.tasks'])

app.config_from_object('task.config')

if __name__ == '__main__':
    app.start()
