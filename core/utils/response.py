#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp_jinja2
from aiohttp import web


async def http_400_response(error_reason):
    return web.json_response({
        'status': 'error',
        'content': error_reason
    }, status=400)


async def http_401_response(error_reason):
    return web.json_response({
        'status': 'error',
        'content': error_reason
    }, status=401)


async def http_404_response(request, msg='Page Not Found!'):
    res = aiohttp_jinja2.render_template('error/404.html', request, {'msg': msg})
    res.set_status(404)
    return res