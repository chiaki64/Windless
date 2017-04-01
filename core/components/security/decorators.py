#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
from aiohttp import web
from aiohttp.abc import AbstractView
from aiohttp_security import permits


# def _require(permission=None):
#     def wrapper(func):
#         @functools.wraps(func)
#         async def wrapped(args):
#             if isinstance(args, AbstractView):
#                 request = args.request
#             else:
#                 request = args
#             has_perm = await permits(request, 'Administrator')
#             if not has_perm:
#                 raise web.HTTPForbidden()
#
#             if isinstance(args, AbstractView):
#                 return await func(args)
#             return await func(args)
#
#         return wrapped
#
#     return wrapper


def require(func):
    @functools.wraps(func)
    async def wrapper(*args):
        if isinstance(args[-1], AbstractView):
            request = args[-1].request
        else:
            request = args[-1]
        has_perm = await permits(request, 'Administrator')
        if not has_perm:
            raise web.HTTPForbidden()

        if isinstance(args, AbstractView):
            return await func(*args)
        return await func(*args)
    return wrapper