#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import time
import misaka
import pyotp
import pytz

from bs4 import BeautifulSoup
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
    publish_data = await request.app.redis.lget('Archive', isdict=True)
    length = len(publish_data if keys_array is None else keys_array)
    total = int(length / page_size) + (0 if int(length / page_size) == (length / page_size) else 1)

    try:
        left = (page - 1) * page_size
        right = page * page_size
        if left + 1 > count:
            raise InvalidPage
        elif count < right:
            right = count
    except InvalidPage:
        return {'exit': 1, 'total': total}

    keys_array = [i['id'] for i in publish_data] if keys_array is None else keys_array
    keys = [keys_array[i] for i in range(left, right)]
    result = await request.app.redis.get_list('Article', keys=keys)

    return {'exit': 0, 'data': result, 'total': total}


def timezone(local='Asia/Shanghai'):
    return pytz.timezone(local)


def todate(stamps, formatted=None, tz=timezone()):
    if formatted is None:
        return datetime.datetime.fromtimestamp(float(stamps), tz)
    return datetime.datetime.fromtimestamp(float(stamps), tz).strftime(formatted)


def rebuild_html(html):
    # 文章分割
    desc = html[:html.find('<hr>', 1)]
    # 删除分割线
    html = html.replace('<hr>', '', 1)
    soup = BeautifulSoup(html, 'html.parser')
    # 增加lazyload标记
    for img in soup.find_all('img'):
        try:
            src = img['data-src']
        except KeyError:
            try:
                src = img['src']
            except KeyError:
                src = ''

        try:
            if 'lazyload' in img['class']:
                continue
        except KeyError:
            img['class'] = []
        img['class'].append('lazyload')
        img['data-src'] = src
        del img['src']

    return str(soup), desc
