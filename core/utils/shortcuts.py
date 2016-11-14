#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import yaml
import misaka


async def word_count(redis):
    # TODO:简单的字数统计
    li = await redis.get_list('Article')
    length = 0
    for i in li:
        length += len(i['text'])
    s = str(round(length / 1000, 2)) + 'k'
    # print(s)
    return s


def load_config(path=''):
    import socket
    try:
        config = yaml.load(open(path + ('./eternity.yaml' if path == '' else '/eternity.yaml')))
    except TypeError:
        config = {}
    config['tk'] = b'\x9f?\x05\xb90\x01R\xb9\xc0\xa5V`\xb3\xaa\xf3\xa0]\xceN\xb0C\xcc\x9d=~\xa5U\xc2W\x88\xd2\xc4'
    if config['env']['hostname'] == socket.gethostname():
        config['dev'] = True
    else:
        config['dev'] = False
    return dict({}, **config)


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
    print(os.path.abspath(os.curdir))
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
