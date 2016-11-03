#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp_auth.auth.ticket_auth import TktAuthentication
from utils.shortcuts import load_config

COOKIE_AUTH_KEY = 'aiohttp_auth.auth.CookieTktAuthentication'

config = load_config()
dev = config.get('dev')


class CookieTktAuthentication(TktAuthentication):
    async def remember_ticket(self, request, ticket):

        request[COOKIE_AUTH_KEY] = ticket

    async def forget_ticket(self, request):

        request[COOKIE_AUTH_KEY] = ''

    async def get_ticket(self, request):

        return request.cookies.get(self.cookie_name, None)

    async def process_response(self, request, response):

        await super().process_response(request, response)
        if COOKIE_AUTH_KEY in request:
            if response.started:
                raise RuntimeError("Cannot save cookie into started response")

            cookie = request[COOKIE_AUTH_KEY]
            if cookie == '':
                response.del_cookie(self.cookie_name)
            else:
                if dev:
                    response.set_cookie(self.cookie_name, cookie, httponly=True)
                else:
                    response.set_cookie(self.cookie_name, cookie, secure=True, httponly=True)