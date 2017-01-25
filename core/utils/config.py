#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml

config = {}
dev = False
maintain = True


def load(path=''):
    import socket
    global config, dev, maintain
    try:
        print(os.getcwd())
        config = yaml.load(open(path + ('./eternity.yaml' if path == '' else '/eternity.yaml')))
    except TypeError:
        config = {}
    config['tk'] = b'\x9f?\x05\xb90\x01R\xb9\xc0\xa5V`\xb3\xaa\xf3\xa0]\xceN\xb0C\xcc\x9d=~\xa5U\xc2W\x88\xd2\xc4'
    # 临时方案
    flag = False
    try:
        if os.environ['env'] == 'dev':
            flag = True
    except KeyError:
        pass

    if config['env']['hostname'] == socket.gethostname() or flag:
        config['dev'] = True
        dev = True
    else:
        config['dev'] = False
    if 'maintain' not in config['server']:
        config['server']['maintain'] = False
        merge_config(config)
    maintain = config['server']['maintain']
    return dict({}, **config)


def dump_config(data=None, path=''):
    try:
        yaml.dump(data, open(path + ('./eternity.yaml' if path == '' else '/eternity.yaml'), 'w'))
    except:
        pass


def merge_config(config, path=''):
    try:
        config.pop('tk')
        config.pop('dev')
        dump_config(config)
    except:
        return False
    return True


load()
