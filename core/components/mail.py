#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from getpass import getpass
from utils import load_config

config = load_config()
dev = config.get('dev')


class Mail:
    def __init__(self):
        pass

    def server(self, host=config['mail']['host'], port=config['mail']['port']):
        server = smtplib.SMTP_SSL(host, port)
        server.login(config['mail']['account'], config['mail']['password'])

    @property
    def message(self, _from, _to, subject, content):
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = _from
        msg['To'] = _to
        msg['Subject'] = Header(subject, 'utf-8')
        return msg





