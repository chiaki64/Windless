#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import functools
from aiohttp import web
from aiohttp.abc import AbstractView
from components.auth.auth import get_auth
from aiohttp_jinja2 import APP_KEY, render_template

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


def geass(template_name, *, app_key=APP_KEY, encoding='utf-8', status=200):

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            if asyncio.iscoroutinefunction(func):
                coro = func
            else:
                coro = asyncio.coroutine(func)
            context = await coro(*args)

            if isinstance(context, web.StreamResponse):
                return context
            if isinstance(args[0], AbstractView):
                request = args[0].request
            else:
                request = args[-1]

            try:
                if 'identifier' in context:
                    # if isinstance(context['identifier'], tuple):
                    #     context['PAGE_IDENTIFIER'] = request.app.router[context['identifier'][0]].url(
                    #         parts={'id': context['identifier'][1]}
                    #     )
                    context['PAGE_IDENTIFIER'] = request.app.router[context['identifier']].url()

                if (await get_auth(request)) is None:
                    context['isauth'] = False
                else:
                    context['isauth'] = True
            except:
                context = await coro(*args)

            response = render_template(template_name, request, context,
                                       app_key=app_key, encoding=encoding)
            response.set_status(status)
            return response
        return wrapped
    return wrapper
