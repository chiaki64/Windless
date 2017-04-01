#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import socket
import secrets
import string
from collections import ChainMap
from utils.abstract import Singleton


class Config(metaclass=Singleton):
    def __init__(self):
        self.dev = False
        self.maintain = False
        self.config = {}
        self.eternity = {}
        self.redis_ip = ''
        self.template_addr = ''
        self.load()

    def load(self):
        (eternity, instant) = ({}, {
            'tk': b'\x9f?\x05\xb90\x01R\xb9\xc0\xa5V`\xb3\xaa\xf3\xa0]\xceN\xb0C\xcc\x9d=~\xa5U\xc2W\x88\xd2\xc4'
        })
        try:
            with open('./eternity.yaml') as file:
                eternity = yaml.load(file)
            if not eternity:
                raise ValueError
        except (TypeError, FileNotFoundError, ValueError):
            raise SystemExit('Please configure eternity.yaml correctly.')

        if eternity['env']['hostname'] == socket.gethostname():
            self.dev = True

        if 'maintain' not in eternity['server']:
            self.maintain = eternity['server']['maintain'] = False
            self.dumps(eternity)

        if 'otp_key' not in eternity['admin'] or eternity['admin']['otp_key'] == '':
            eternity['admin']['otp_key'] = ''.join(
                map(lambda x: secrets.choice(f'{string.ascii_uppercase}234567'), [1] * 16)
            )
            self.dumps(eternity)

        if 'identity' not in eternity['admin'] or eternity['admin']['identity'] == '':
            eternity['admin']['identity'] = ''.join(
                map(lambda x: secrets.choice(f'{string.ascii_letters}{string.digits}'), [1] * 4)
            )
            self.dumps(eternity)

        if self.dev:
            self.redis_ip = eternity['redis']['host']
            self.template_addr = f"./resource/templates/{eternity['server']['template']}"
        else:
            self.redis_ip = os.environ['REDIS_PORT_6379_TCP_ADDR']
            self.template_addr = f"/code/core/resource/templates/{eternity['server']['template']}"

        self.eternity = eternity
        self.config = ChainMap(instant, eternity)

    def __getattr__(self, item):
        try:
            return self.config[item]
        except KeyError:
            return None

    @staticmethod
    def dumps(data=None):
        if data is None:
            pass
        try:
            with open('./eternity.yaml', 'w') as file:
                yaml.dump(data, file)
        except:
            pass

config = Config()
# print(config.dev)
# c1 = Config()
# c1.dev = False
# print(c1.dev, config.dev)
