#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import aiohttp_jinja2
from aiohttp import web


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            if response.status == 404:
                return await handler_not_found(request)
            elif response.status == 403:
                return web.HTTPFound('/auth/login')
            return response
        except web.HTTPException as ex:
            if ex.status == 404:
                return await handler_not_found(request)
            elif ex.status == 403:
                return web.HTTPFound('/auth/login')
            raise

    return middleware_handler


async def handler_not_found(request, msg='Page Not Found!'):
    res = aiohttp_jinja2.render_template('error/404.html', request, {'msg': msg})
    res.set_status(404)
    return res


async def http_400_response(error_reason):
    return web.json_response({
        'status': 'error',
        'content': error_reason
    }, status=400)


async def word_count(redis):
    # TODO:简单的字数统计
    li = await redis.get_list('Article')
    length = 0
    for i in li:
        length += len(i['text'])
    s = str(round(length / 1000, 2)) + 'k'
    print(s)
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


class InvalidPage(Exception):
    pass

