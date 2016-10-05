#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Server

import asyncio
import jinja2
import os
import aioredis
import aiohttp_jinja2
import aiohttp_debugtoolbar
from aiohttp import web
from aiohttp_auth import auth
from aiohttp_session import session_middleware
from aiohttp_debugtoolbar import toolbar_middleware_factory
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from routes import routes
from memory import RedisFilter
from eternity import server, dev, admin, memory_conf
from utils import error_middleware

import uvloop


async def init(loop):
    # Auth
    policy = auth.CookieTktAuthentication(os.urandom(
        32) if not dev else b'\x9f?\x05\xb90\x01R\xb9\xc0\xa5V`\xb3\xaa\xf3\xa0]\xceN\xb0C\xcc\x9d=~\xa5U\xc2W\x88\xd2\xc4',
                                          7200, include_ip=True)
    # Middleware
    middlewares = [session_middleware(EncryptedCookieStorage(os.urandom(
        32) if not dev else b'\x9a\xd7\x9bLU\xb7\xb0\x17\xa8x\xab\x8f\xfd\xd1\x18I\xc5{\xa0\xf6\x06\xf1\xbe\xafHG7bB\x03]9')),
                   auth.auth_middleware(policy),
                   error_middleware]
    if dev:
        middlewares.append(toolbar_middleware_factory)
    # 初始化
    app = web.Application(loop=loop,
                          middlewares=middlewares)

    # 初始化Redis / 使用Pool
    if dev:
        redis_ip = '127.0.0.1'
        template_addr = './templates'
    else:
        redis_ip = os.environ["REDIS_PORT_6379_TCP_ADDR"]
        template_addr = '/code/core/templates'

    redis = await aioredis.create_redis((redis_ip, memory_conf['port']), loop=loop)
    app.redis = RedisFilter(redis)

    # 初始化管理员帐号
    await app.redis.set('User', admin, many=False)
    # 初始化 jinja2
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader(template_addr))

    print(os.path.abspath('.'))

    # 注册路由及静态路由
    for route in routes:
        print('Add route %s %s => %s' % (route[0], route[1], route[2].__name__))
        app.router.add_route(route[0], route[1], route[2], name=route[3])

    app.router.add_static('/static/',
                          path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
                          name='static')

    # Debug
    if dev:
        aiohttp_debugtoolbar.setup(app)

    _handler = app.make_handler()
    _srv = await loop.create_server(_handler, server['ip'], server['port'])
    print('Server started at http://%s:%s...' % (server['ip'], server['port']))
    return _srv, _handler, app


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
srv, handler, app = loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    loop.run_until_complete(handler.finish_connections())
