#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import time
import pytz


def now():
    return int(time.time())


def timezone(local='Asia/Shanghai'):
    return pytz.timezone(local)


def todate(stamps, formatted=None, tz=timezone()):
    if formatted is None:
        return datetime.datetime.fromtimestamp(float(stamps), tz)
    return datetime.datetime.fromtimestamp(float(stamps), tz).strftime(formatted)
