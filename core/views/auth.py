#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import simplejson as json
from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid
from components.eternity import config
from components.security.auth import auth, check_credentials, check_method
from components.security.decorators import require
from components.security.factor import (sign,
                                        enroll,
                                        bind,
                                        verify)
from utils.abstract import AbsWebView
from utils.period import todate
from utils.response import geass, http_400_response


class LoginView(AbsWebView):
    async def get(self):
        u2f, req, method = False, [], self._get('method', None)
        if config.admin['u2f'] and method is None:
            u2f = True
            identity = config.admin['identity']
            users = await self.redis.get('Auth.U2F') or {}
            try:
                user = users[identity]
                users[identity], req = await sign(user)
                await self.redis.set('Auth.U2F', users, many=False)
            except KeyError:
                pass
        elif method == 'common':
            u2f = False

        if await auth(self.request):
            return web.HTTPFound('/manage')
        return geass({
            'u2f': u2f,
            'request': req
        }, self.request, 'public/login.html')

    async def post(self):
        form = await self.request.post()
        identity = config.admin['identity']
        # account = await self.redis.get('User')
        response = web.HTTPFound('/manage')

        if config.admin['u2f'] and '_method' not in form:
            users = await self.redis.get('Auth.U2F') or {}
            users[identity], ok = await verify(users[identity], dict(await self.request.post()))
            if ok:
                await self.redis.set('Auth.U2F', users, many=False)
                await remember(self.request, response, identity)
                return response
        elif form['_method'] == 'common':
            method = check_method(form.get('email').lower())
            # TODO:验证邮箱是否合法
            if await check_credentials(self.redis, identity, form.get('password')):
                await remember(self.request, response, identity)
                return response
        return web.HTTPFound('/auth/login')


class LogoutView(AbsWebView):
    @require
    async def get(self):
        response = web.HTTPFound('/')
        await forget(self.request, response)
        return response


class EnrollView(AbsWebView):
    async def get(self):
        username = config.admin['identity']
        users = await self.redis.get('Auth.U2F') or {}
        if username not in users:
            users[username] = {}

        users[username], req = await enroll(users[username])
        await self.redis.set('Auth.U2F', users, many=False)
        return geass({
            'request': req
        }, self.request, 'public/yubi_auth.html')

    async def post(self):
        username = config.admin['identity']
        users = await self.redis.get('Auth.U2F') or {}
        data = dict(await self.request.post())
        data['date'] = todate(str(time.time()), '%b %d,%Y')
        users[username], ok = await bind(users[username], data)
        if ok:
            await self.redis.set('Auth.U2F', users, many=False)
            return web.json_response(json.dumps(True))
        return web.json_response(json.dumps(False))
