#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aioredis
import os
import uvloop
import jinja2
import aiohttp_jinja2
from aiohttp import web
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy
from aiohttp_session import setup as setup_session
from aiohttp_session.redis_storage import RedisStorage
from components.memory import RedisFilter
from components.eternity import config
from components.logger import logger, formatters
from components.router import compass
from components.security.auth import (RedisAuthorizationPolicy,
                                      encrypt)
from utils.middleware import (error_middleware,
                              maintain_middleware)


async def init(loop):
    # Middlewares
    middlewares = [
        error_middleware,
        maintain_middleware,
    ]

    # init server
    app = web.Application(loop=loop,
                          middlewares=middlewares)

    redis = await aioredis.create_redis((config.redis_ip, config.redis['port']), loop=loop)
    app.redis = RedisFilter(redis)

    # Register admin account
    if await app.redis.get('User') is None:
        await app.redis.set('SecretKey', os.urandom(16), many=False)
        config.admin['password'] = await encrypt(app.redis, config.admin['password'])
        config.admin['permission'] = 0x0f
        await app.redis.set('User', config.admin, many=False)

    # Init Profile
    if await app.redis.get('Profile') is None:
        await app.redis.set('Profile', {
            'name': config.rss['author'],
            'link_desc': '',
            'text': ''
        }, many=False)

    # Security
    setup_session(app, RedisStorage(await aioredis.create_pool((config.redis_ip, 6379)), cookie_name='Windless_Session'))
    setup_security(app,
                   SessionIdentityPolicy(),
                   RedisAuthorizationPolicy(redis))

    await compass(app.router)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(config.template_addr))

    _handler = app.make_handler(
        access_log=logger,
        access_log_format=formatters
    )
    _srv = await loop.create_server(_handler, config.server['host'], config.server['port'])
    print('Server started at http://%s:%s...' % (config.server['host'], config.server['port']))
    return _srv, _handler, app


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
srv, handler, app = loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    loop.run_until_complete(handler.finish_connections())
