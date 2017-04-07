#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp import web
from aiohttp_jinja2 import APP_KEY, render_template
from utils.constant import CONST


def geass(context, request, tmpl=None, *, app_key=APP_KEY, encoding='utf-8', status=200):
    # print('path->', request.url)
    if tmpl is None:
        return web.json_response(context)
    try:
        if 'identifier' in context:
            context['PAGE_IDENTIFIER'] = request.app.router[context['identifier']].url()
            # Auth
        context['drawer_category'] = CONST.CATEGORY
    except:
        raise RuntimeError

    response = render_template(tmpl, request, context,
                               app_key=app_key, encoding=encoding)
    response.set_status(status)
    return response


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
    res = render_template('error/404.html', request, {'msg': msg})
    res.set_status(404)
    return res


async def http_503_response():
    return web.json_response({
        'status': 'error',
        'content': 'Service Temporarily Unavailable'
    }, status=503)