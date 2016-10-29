#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from .shortcuts import (http_400_response, http_404_response)


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
