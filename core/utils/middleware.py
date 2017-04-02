#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from components.eternity import config
from .response import (http_404_response, http_503_response)
from components.security.auth import auth


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            if response.status == 404:
                return await http_404_response(request)
            elif response.status == 403:
                return web.HTTPFound('/auth/login')
            return response
        except web.HTTPException as ex:
            if ex.status == 404:
                return await http_404_response(request)
            elif ex.status == 403:
                return web.HTTPFound('/auth/login')
            raise
    return middleware_handler


async def maintain_middleware(app, handler):
    async def middleware_handler(request):
        if config.server['maintain'] is False or list(filter(lambda x: x in request.path, ['manage', 'auth', 'static'])) \
                or await auth(request):
            response = await handler(request)
            return response
        return await http_503_response()
    return middleware_handler


