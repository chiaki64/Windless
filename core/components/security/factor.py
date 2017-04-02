#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from u2flib_server.u2f import (begin_registration,
                               begin_authentication,
                               complete_registration,
                               complete_authentication)
from components.eternity import config

facet = config.rss['link']


async def enroll(user):
    enroll = begin_registration(facet, user.get('_u2f_devices_', []))
    user['_u2f_enroll_'] = enroll.json
    return user, json.dumps(enroll.data_for_client)


async def bind(user, data):
    response = data['tokenResponse']
    enroll = user.pop('_u2f_enroll_')
    try:
        device, cert = complete_registration(enroll, response, [facet])
        device['deviceName'] = data['deviceName']
        device['registerDate'] = data['date']
        user.setdefault('_u2f_devices_', []).append(json.dumps(device))
    except AttributeError:
        return user, False
    return user, True


async def sign(user):
    challenge = begin_authentication(facet, user.get('_u2f_devices_', []))
    user['_u2f_challenge_'] = challenge.json
    return user, json.dumps(challenge.data_for_client)


async def verify(user, data):
    challenge = user.pop('_u2f_challenge_')
    try:
        complete_authentication(challenge, data['tokenResponse'], [facet])
    except AttributeError:
        return user, False
    return user, True
