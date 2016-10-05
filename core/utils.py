#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
            raise

    return middleware_handler


async def handler_not_found(request, msg='1'):
    res = aiohttp_jinja2.render_template('error/404.html',
                                         request,
                                         {'msg': msg})
    res.set_status(404)
    return res


async def word_count(redis):
    # 简单的字数统计
    li = await redis.get_list('Article')
    length = 0
    for i in li:
        length += len(i['text'])
    s = str(round(length / 1000, 2)) + 'k'
    print(s)
    return s
