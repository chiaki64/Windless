#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Server

import asyncio
import jinja2
import os
import uvloop
import aioredis
import aiohttp_jinja2
import aiohttp_debugtoolbar
import pyotp
from aiohttp import web
from aiohttp_auth import auth
from aiohttp_session import session_middleware
from aiohttp_debugtoolbar import toolbar_middleware_factory
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from routes import routes
from memory import RedisFilter
from components import auth as wind_auth
from utils.middlewares import error_middleware
from utils.shortcuts import load_config, merge_config

config = load_config()
dev = config.get('dev')


async def init(loop):
    # init secret key
    if 'secret_key' not in config['admin'] or config['admin']['secret_key'] == '':
        config['admin']['secret_key'] = pyotp.random_base32()
        merge_config(config)
    # Auth
    policy = wind_auth.CookieTktAuthentication(os.urandom(
        32) if not dev else config.get('tk'), 7200, include_ip=True, cookie_name='WIND_TK')
    # Middleware
    middlewares = [
        session_middleware(EncryptedCookieStorage(os.urandom(
            32) if not dev else config.get('tk'))),
        auth.auth_middleware(policy),
        error_middleware
    ]
    if dev:
        middlewares.append(toolbar_middleware_factory)
    # 初始化
    app = web.Application(loop=loop,
                          middlewares=middlewares)

    # 初始化Redis / 使用Pool
    if dev:
        redis_ip = config['memory']['host']
        template_addr = './templates'
    else:
        redis_ip = os.environ["REDIS_PORT_6379_TCP_ADDR"]
        template_addr = '/code/core/templates'

    redis = await aioredis.create_redis((redis_ip, config['memory']['port']), loop=loop)
    app.redis = RedisFilter(redis)

    # 初始化管理员帐号
    await app.redis.set('User', config['admin'], many=False)
    # 初始化 jinja2
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader(template_addr))

    # 注册路由及静态路由
    for route in routes:
        print('Add route %s %s => %s' % (route[0], route[1], route[2].__name__))
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    # For Dev only
    if dev:
        app.router.add_static('/static/',
                              path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                              name='static')

    # Debug
    if dev:
        aiohttp_debugtoolbar.setup(app)

    _handler = app.make_handler()
    _srv = await loop.create_server(_handler, config['server']['host'], config['server']['port'])
    print('Server started at http://%s:%s...' % (config['server']['host'], config['server']['port']))
    return _srv, _handler, app


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
srv, handler, app = loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    loop.run_until_complete(handler.finish_connections())
