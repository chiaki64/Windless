#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from aiohttp_security.abc import AbstractAuthorizationPolicy
from aiohttp_security import authorized_userid
from components.memory import RedisFilter
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey

# Will be use in the future
PERMISSIONS = {
    'view': 0x01,
    'edit': 0x02,
    'write': 0x04,
    'manage': 0x08
}


class RedisAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, redis):
        self.conn = RedisFilter(redis)

    async def authorized_userid(self, identity):
        if await exist(self.conn, identity) is not None:
            return identity
        return None

    async def permits(self, identity, permission=0x08, context=None):
        if identity is None:
            return False
        user = await exist(self.conn, identity)
        if user is not None:
            if user['permission'] & 0x0f > 0:
                return True
        return False


async def check_credentials(redis: RedisFilter, identity, password):
    user = await exist(redis, identity)
    if user is not None:
        if await verify(redis, password, user['password']):
            return True
    return False


async def repeat_check(redis: RedisFilter, username):
    if await exist(redis, username) is not None:
        return False
    return True


async def encrypt(redis: RedisFilter, password):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes(await redis.get('SecretKey')),
        iterations=10000,
        backend=default_backend()
    )
    token = kdf.derive(str.encode(password))
    return token


async def verify(redis, password, token):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes(await redis.get('SecretKey')),
        iterations=10000,
        backend=default_backend()
    )
    try:
        if token != '' and kdf.verify(str.encode(password), token) is None:
            return True
    except InvalidKey:
        pass
    return False


def check_method(key):
    if re.match('^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$', key) is not None:
        method = 'email'
    else:
        method = 'username'
    return method


async def exist(redis, identity):
    user = await redis.get('User')
    if identity == user['identity']:
        return user
    return None

async def auth(request):
    if await authorized_userid(request) is None:
        return False
    return True
