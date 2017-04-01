#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import misaka
import pyotp
from bs4 import BeautifulSoup
from utils.exception import InvalidPage


async def paginate(request, *, page=1, page_size=10, keys_array=None, istop=False):
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
    publish_data = await request.app.redis.lget('Archive', isdict=True, reverse=True)
    length = len(publish_data if keys_array is None else keys_array)
    total = int(length / page_size) + (0 if int(length / page_size) == (length / page_size) else 1)

    try:
        left = (page - 1) * page_size
        right = page * page_size
        # Fix error when no article in database
        if left + 1 > count > 0:
            raise InvalidPage
        elif count < right:
            right = count
    except InvalidPage:
        return {'exit': 1, 'total': total}

    keys_array = [i['id'] for i in publish_data] if keys_array is None else keys_array
    keys = [keys_array[i] for i in range(left, right)]
    result = await request.app.redis.get_list('Article', keys=keys, istop=istop)

    return {'exit': 0, 'data': result, 'total': total}


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


def render(content):
    return misaka.html(content, extensions=('fenced-code', 'strikethrough',))


async def word_count(redis):
    # TODO:简单的字数统计
    li = await redis.get_list('Article')
    length = 0
    for i in li:
        length += len(i['text'])
    s = str(round(length / 1000, 2)) + 'k'
    return s


def otp_url(secret, mail, name):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(mail, name)
