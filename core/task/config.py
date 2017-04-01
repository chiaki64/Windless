#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from components.eternity import config

CELERY_RESULT_BACKEND = f'redis://{config.redis_ip}:6379/0'
BROKER_URL = f'redis://{config.redis_ip}:6379/1'

CELERY_TIMEZONE = 'Asia/Shanghai'

from celery.schedules import crontab

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'add-every-monday-morning': {
        'task': 'task.tasks.restart',
        'schedule': crontab(hour=17, minute=30, day_of_week=1),
        'args': (1,),
    },
    # 'add-every-10-sec': {
    #     'task': 'task.tasks.add',
    #     'schedule': timedelta(seconds=10),
    #     'args': (16, 16),
    # },
}
# celery -A task worker -B -l info
# nohup celery -A task worker -B -l info > /dev/null 2>../log/celery.log
