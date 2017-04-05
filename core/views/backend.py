#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import simplejson as json
from aiohttp import web
from components.eternity import config
from components.security.decorators import require
from utils.abstract import AbsWebView
from utils.constant import CATEGORY
from utils.period import todate
from utils.response import (geass,
                            http_400_response)
from utils.shortcut import (rebuild_html,
                            render,
                            word_count,
                            otp_url)
from utils.serializer import ArticleSer


@require
class IndexView(AbsWebView):
    async def get(self):
        count = await self.redis.count('Article')
        try:
            pub_cnt = len(await self.redis.get('Archive'))
        except TypeError:
            pub_cnt = 0
        cat_cnt = {}
        for cat in CATEGORY:
            cat_cnt[cat] = (await self.redis.lget(f'Category.{cat}')).__len__()
        return geass({
            'articles': {
                'count': count,
                'publish': pub_cnt,
                'category': cat_cnt
            }
        }, self.request, 'backend/index.html')


@require
class ArticleEditView(AbsWebView):
    async def get(self):
        return geass({}, self.request, 'backend/edit.html')

    async def post(self):
        form = dict(await self.request.post(), **{'edit': True})
        ser = ArticleSer(form=form)

        if ser.is_valid():
            # print(ser.data)
            id = await self.redis.set('Article', ser.data, id=ser.data['id'])
        else:
            return await http_400_response('article error')

        # Save to category
        await self.redis.lpush('Category.' + form['category'], id)
        # Save to Archive
        if form['open'] == 'on':
            await self.redis.lpush('Archive', {
                'id': id,
                'title': form['title'],
                'category': form['category'],
                'created_time': form['created_time']
            }, isdict=True)
        # Save to Top
        if form['top'] == 'on':
            await self.redis.lpush('Top', id)
        await self.redis.set('Data.WordCount', await word_count(self.redis), many=False)
        # Create Backup
        raise web.HTTPFound('/')


@require
class ArticleUpdateView(AbsWebView):
    async def get(self):
        # 不存在的id报错
        article_id = self.match['id']
        data = await self.redis.get('Article', article_id)
        data['text'] = data['text'].replace('\\r', '\\\\r').replace('\r\n', '\\n').replace('"', '\\"')

        return geass({
            'article': data
        }, self.request, 'backend/update.html')

    async def post(self):
        form = dict(await self.request.post())
        (id, new_id) = (self.match['id'], form['id'])
        origin = await self.redis.get('Article', id)
        form['updated_time'] = form['time']
        if form['citation'] == 'None':
            del form['citation']
        data = dict(origin, **form)

        ser = ArticleSer(form=data)

        if ser.is_valid():
            if id != new_id:
                await self.redis.delete('Article', id=id)
            await self.redis.set('Article', ser.data, id=new_id)
        else:
            return await http_400_response('article error')

        # Change Category
        if origin['category'] != data['category'] or new_id != id:
            await self.redis.lrem('Category.' + origin['category'], id)
            await self.redis.lpush('Category.' + data['category'], new_id)
        # Change Archive
        await self.redis.lrem('Archive', id, isdict=True)
        if ((origin['open'] != data['open'] and origin['open'] == 'on') or (data['open'] == 'no')) and new_id == id:
            pass
        else:
            await self.redis.lpush('Archive', {
                'id': new_id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)

        if form['top'] == 'no':
            await self.redis.lrem('Top', id)
        elif form['top'] == 'on':
            await self.redis.lpush('Top', id)
        await self.redis.set('Data.WordCount', await word_count(self.redis), many=False)
        raise web.HTTPFound('/')


@require
class ArticleListView(AbsWebView):
    async def get(self):
        data = await self.redis.get_list('Article', isauth=True)
        return geass({
            'articles': data
        }, self.request, 'backend/articles.html')


@require
class ProfileView(AbsWebView):
    async def get(self):
        data = await self.redis.get('Profile')
        if data is None:
            data = dict(name='', text='', link_desc='')
        if 'link_desc' not in data:
            data['link_desc'] = ''
        return geass({
            'profile': {
                'name': data['name'],
                'avatar': '/static/img/avatar.jpg',
                'link_desc': data['link_desc'],
                'text': data['text'].replace('\\r', '\\\\r').replace('\r\n', '\\n').replace('\"', '\\"')
                    .replace('<', '&lt;').replace('>', '&gt;')
            }
        }, self.request, 'backend/profile.html')

    async def post(self):
        data = dict({}, **await self.request.post())
        data['text'] = data['text'].replace('&lt;', '<').replace('&gt;', '>')
        data['html'] = render(data['text'])
        path = './static/img/avatar.jpg'
        if data['avatar'] != b'':
            file = open(path, 'wb')
            file.write(data['avatar'].file.read())
        if 'avatar' in data:
            del data['avatar']
        data['updated_date'] = time.strftime('%b.%d %Y', time.localtime())
        await self.redis.set('Profile', data, many=False)
        return web.HTTPFound('/manage/profile')


@require
class ConfigView(AbsWebView):
    async def get(self):
        key = config.admin['otp_key']
        return geass({
            'secret': key,
            'otp_url': otp_url(key, config.admin['email'], config.admin['username']),
            'otp': config.admin['otp'],
            'maintain': config.server['maintain']
        }, self.request, 'backend/config.html')

    async def post(self):
        data = await self.request.post()

        def control(name, group):
            if name in data:
                # print(data[name])
                if data[name] == 'open':
                    config.eternity[group][name] = True
                elif data[name] == 'close':
                    config.eternity[group][name] = False
                config.dumps(config.eternity)

        control('otp', 'admin')
        control('maintain', 'server')

        return geass({
            'status': 200
        }, self.request)


@require
class LinksView(AbsWebView):
    async def get(self):
        data = await self.redis.lget('Link', isdict=True, reverse=False)
        if data is None:
            data = []
        return geass({
            'friends': data,
            'len': len(data) + 1
        }, self.request, 'backend/link.html')

    async def post(self):
        data = dict({}, **await self.request.post())
        data.pop('_id')
        await self.redis.lpush('Link', data, isdict=True)
        return web.json_response({
            'status': 200
        })

    async def put(self):
        data = dict({}, **await self.request.post())
        # print(data)
        _id = data['_id']
        data.pop('_id')
        await self.redis.lset('Link', _id, data, isdict=True, _key='order')
        return web.json_response({
            'status': 200
        })


# @require
# class LinksUpdateView(AbsWebView):
#     async def get(self):
#         id = self.match['id']
#         data = await self.redis.lget('Link', isdict=True)
#         if data is None:
#             return await http_400_response('Data Error')
#         for item in data:
#             if item['id'] == id:
#                 return geass({
#                     'link': item
#                 }, self.request, 'backend/simple_link.html')
#         return await http_400_response('Data Error')
#
#     async def post(self):
#         data = dict({}, **await self.request.post())
#         _id = data['_id']
#         data.pop('_id')
#         await self.redis.lset('Link', _id, data, isdict=True)
#         raise web.HTTPFound('/manage/links')
#
#     async def delete(self):
#         await self.redis.lrem('Link', isdict=True)
#         return web.json_response({'status': 'success'})


@require
class GuestBookView(AbsWebView):
    async def get(self):
        data = await self.redis.lget('GuestBook', isdict=True, reverse=False)
        if data is None:
            data = []
        return geass({
            'len': len(data) + 1
        }, self.request, 'backend/guestbook.html')

    async def post(self):
        data = dict({}, **await self.request.post())
        data['created_time'] = str(time.time())
        data['date'] = todate(data['created_time'], '%b.%d')
        data['html'] = render(data['text'])
        await self.redis.lpush('GuestBook', data, isdict=True)
        raise web.HTTPFound('/guest-book')


@require
class SecurityView(AbsWebView):
    async def get(self):
        username = config.admin['identity']
        users = await self.redis.get('Auth.U2F') or {}
        if username in users:
            try:
                devices = [json.loads(d) for d in users[username]['_u2f_devices_']]
            except KeyError:
                devices = []
        else:
            devices = []
        return geass({
            'u2f': config.admin['u2f'],
            'devices': devices
        }, self.request, 'backend/security.html')

    async def post(self):
        data = await self.request.post()

        def control(name, group):
            if name in data:
                if data[name] == 'open':
                    config.eternity[group][name] = True
                elif data[name] == 'close':
                    config.eternity[group][name] = False
                config.dumps(config.eternity)

        control('u2f', 'admin')
        return web.json_response({'status': 200})

    async def put(self):
        from components.security.auth import encrypt
        data = await self.request.post()

        value = config.admin
        value['password'] = await encrypt(self.redis, data['password'])
        value['permission'] = 0x0f
        await self.redis.set('User', value, many=False)
        return web.json_response({
            'status': 200
        })
