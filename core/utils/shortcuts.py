#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import misaka
import pyotp

from .exception import InvalidPage


async def compass(data):
    route_list = []
    for cat in data:
        for method in data[cat]['data']:
            for item in data[cat]['data'][method]:
                route_list.append((method,) + (data[cat]['prefix'] + item[0],) + item[1:])
    return route_list


async def word_count(redis):
    # TODO:简单的字数统计
    li = await redis.get_list('Article')
    length = 0
    for i in li:
        length += len(i['text'])
    s = str(round(length / 1000, 2)) + 'k'
    return s


async def create_backup(redis, *, dev=True):

    articles = await redis.get_list('Article', isauth=True)
    links = await redis.lget('Link', isdict=True)
    profile = await redis.get('Profile')

    data = {
        'articles': articles,
        'links': links,
        'profile': profile
    }

    name = time.strftime('%Y_%m_%d_%H%M%S', time.localtime(time.time()))
    import os
    # print(os.path.abspath(os.curdir))
    if dev:
        path = './backup/'
    else:
        path = '/code/core/backup/'
    if not os.path.isdir(path):
        os.mkdir(path)
    file = open(path+'windless_' + name + '.json', 'w')
    data = json.dumps(data)
    file.write(data)
    file.close()


def render(content):
    return misaka.html(content, extensions=('fenced-code', 'strikethrough',))


def verify(config, passwd):
    if 'otp' in config['admin'] and config['admin']['otp'] is False:
        return True
    totp = pyotp.TOTP(config['admin']['secret_key'])
    return totp.verify(passwd)


def otp_url(secret, mail, name):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(mail, name)


async def paginate(request, *, page=1, page_size=10, keys_array=None):
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        return {'exit': 1}
    data = await request.app.redis.get_list('Article')
    if page is None:
        return data

    count = len(data) if keys_array is None else len(keys_array)
    try:
        left = (page - 1) * page_size
        right = page * page_size
        if left + 1 > count:
            raise InvalidPage
        elif count < right:
            right = count
    except InvalidPage:
        return {'exit': 1}

    publish_data = await request.app.redis.lget('Archive', isdict=True)
    keys_array = [i['id'] for i in publish_data] if keys_array is None else keys_array
    # print(keys_array)
    keys = [keys_array[i] for i in range(left, right)]
    # print(keys)
    result = await request.app.redis.get_list('Article', keys=keys)

    return {'exit': 0, 'data': result}



