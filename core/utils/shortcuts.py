#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import yaml


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
        default = yaml.load(open('./eternity_default.yaml'))
    except FileNotFoundError:
        path = '/code/core'
        default = yaml.load(open(path + '/eternity_default.yaml'))
    try:
        config = yaml.load(open(path + ('./eternity.yaml' if path == '' else '/eternity.yaml')))
    except TypeError:
        config = {}
    config['tk'] = b'\x9f?\x05\xb90\x01R\xb9\xc0\xa5V`\xb3\xaa\xf3\xa0]\xceN\xb0C\xcc\x9d=~\xa5U\xc2W\x88\xd2\xc4'
    if config['env']['hostname'] == socket.gethostname():
        config['dev'] = True
    else:
        config['dev'] = False
    return dict(default, **config)


async def create_backup(redis, *, env=True):

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
    if env:
        file = open('./backup/windless_' + name + '.json', 'w')
    else:
        file = open('/code/core/backup/' + name + '.json', 'w')
    data = json.dumps(data)
    file.write(data)
    file.close()
