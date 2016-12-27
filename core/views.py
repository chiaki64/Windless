#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Views

import datetime
import re
import time
from aiohttp import web
from components.auth import auth
from components.auth.auth import auth_required
from components.rss import RSS, RSSItem
from components.u2f import *
from utils.config import config, merge_config, dev
from utils.exception import InvalidPage
from utils.response import (http_400_response,
                            http_401_response,
                            http_404_response,
                            geass)
from utils.shortcuts import (word_count,
                             create_backup,
                             render,
                             paginate,
                             otp_url,
                             verify,
                             timezone,
                             todate)


class AbsWebView(web.View):
    def __init__(self, request):
        super(AbsWebView, self).__init__(request)
        self.redis = self.request.app.redis
        self._get = self.request.GET.get
        self.match = self.request.match_info


class IndexView(AbsWebView):
    @geass('public/catalog.html')
    async def get(self):
        page = self._get('page', None)
        if page == 'full':
            # 返回全部文章
            data = await self.redis.get_list('Article')
        else:
            key = self._get('search', None)
            # 若匹配到 search 参数则不分页
            if key is None:
                if page is None:
                    page = 1
                status = await paginate(self.request, page=page)
                if status['exit'] == 0:
                    data = status['data']
                else:
                    return await http_404_response(self.request)
                return {'articles': data, 'page': int(page), 'total': status['total']}
            else:
                data = []
                result = await self.redis.get_list('Article')
                for item in result:
                    if re.search(key, item['text']) or re.search(key, item['title']) or re.search(key, item['tags']):
                        data.append(item)
        return {'articles': data, 'page': 1, 'total': 1}


class ArticleListView(AbsWebView):
    @geass('public/catalog.html')
    async def get(self):
        page = self._get('page', None)
        category = self.match['category'].lower()
        data_list = await self.redis.lget('Category.' + category)

        if page == 'full':
            # TODO: Error
            data = await self.redis.get_list('Article', data_list)
        elif len(data_list) == 0:
            data = []
        else:
            if page is None:
                page = 1
            status = await paginate(self.request, page=page, keys_array=data_list)
            if status['exit'] == 0:
                data = status['data']
            else:
                return await http_404_response(self.request)
            return {'articles': data, 'page': int(page), 'total': status['total'], 'category': category}
        return {'articles': data, 'page': 1}


class ArticleView(AbsWebView):
    @geass('public/article.html')
    async def get(self):
        id = self.match['id']
        if id.isdigit() is False:
            return web.HTTPNotFound()
        data = await self.redis.get('Article', id)
        if data is None:
            return web.HTTPNotFound()

        elif data['open'] is '1':
            user = await auth.get_auth(self.request)
            if user is None:
                return await http_401_response('Not Allow')
        if len(re.findall('[$]{1,2}', data['text'])) > 0:
            math = True
        else:
            math = False
        return {
            "article": data,
            'math': math,
            'PAGE_IDENTIFIER': self.request.app.router['article'].url(
                parts={'id': id}
            ),
            'dev': not dev,
            'comment': True
        }


class ArchiveView(AbsWebView):
    @geass('public/archive.html')
    async def get(self):
        data = await self.redis.lget('Archive', isdict=True)
        dit = {}
        data.sort(key=lambda x: int(todate(x['created_time'], '%Y%m%d')), reverse=True)
        for item in data:
            date = todate(item['created_time'], '%Y年|%m月%d日')
            year, item['day'] = date.split('|')
            if year not in dit:
                dit[year] = []
            dit[year].append(item)
        return {
            'archive': dit,
            'profile': await self.redis.get('Profile'),
            'identifier': 'archive'}


class LinkView(AbsWebView):
    @geass('public/links.html')
    async def get(self):
        data = await self.redis.lget('Link', isdict=True, reverse=False)
        if data is None:
            data = []
        return {
            'friends': data,
            'blog': {
                'name': config['admin']['username'],
                'link': config['blog']['link'],
                'desc': (await self.redis.get('Profile'))['link_desc']
            },
            'identifier': 'links',
            'comment': True
        }


class ProfileView(AbsWebView):
    @geass('public/about.html')
    async def get(self):
        data = await self.redis.get('Profile')
        words = await self.redis.get('Data.WordCount')
        return {
            'profile': data,
            'word_count': words,
            'identifier': 'about',
            'comment': True
        }


class LoginView(AbsWebView):
    @geass('public/login.html')
    async def get(self):
        user = await auth.get_auth(self.request)
        if user is None:
            pass
        else:
            return web.HTTPFound('/manage')

    async def post(self):
        data = await self.request.post()
        account = await self.redis.get('User')
        if account['email'] == data['email'] \
                and account['password'] == data['password'] \
                and verify(config, data['otp']):
            await auth.remember(self.request, account['username'])
            return web.HTTPFound('/manage')
        return web.HTTPFound('/auth/login')


@auth_required
class LogoutView(AbsWebView):
    async def get(self):
        await auth.forget(self.request)
        return web.HTTPFound('/')


@auth_required
class BackendIndexView(AbsWebView):
    @geass('backend/index.html')
    async def get(self):
        # 数据监控 文章情况等
        article_count = await self.redis.count('Article')
        try:
            publish_count = (await self.redis.get('Archive'))['list'].__len__()
        except TypeError:
            publish_count = 0
        category = ['algorithm', 'acgn', 'code', 'daily', 'essay', 'web']
        category_count = {}
        for cat in category:
            category_count[cat] = (await self.redis.lget('Category.' + cat)).__len__()

        return {
            'articles': {
                'count': article_count,
                'publish': publish_count,
                'category': category_count
            }
        }


@auth_required
class BackendArticleEditView(AbsWebView):
    @geass('backend/edit.html')
    async def get(self):
        pass

    async def post(self):
        data = await self.request.post()
        # important
        data = dict({}, **data)
        # 处理迁移文章
        if data['id'] == '':
            data['id'] = None

        data['html'] = render(data['text'])
        data['created_time'] = str(time.time())

        if data['time'] == '':
            data['date'] = todate(data['created_time'], '%b.%d %Y')
        else:
            data['created_time'] = data['time']
            data['date'] = todate(data['created_time'], '%b.%d %Y')
        data.pop('time')

        # 分割文章
        data['desc'] = (data['html'])[:(data['html']).find('<hr>', 1)]
        data['desc_text'] = ((data['text'])[:(data['text']).find('-----', 1)]).replace('\n', ' ')
        # 删除分割线
        data['html'] = data['html'].replace('<hr>', '', 1)

        id = await self.redis.set('Article', data, id=data['id'])
        # 保存到Category
        await self.redis.lpush('Category.' + data['category'], id)
        # 保存到Archive
        if data['open'] is '0':
            await self.redis.lpush('Archive', {
                'id': id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)
        # 更新字数统计
        await self.redis.set('Data.WordCount', await word_count(self.redis), many=False)
        # 备份
        await create_backup(self.redis, dev=config.get('dev'))
        return web.HTTPFound('/')


@auth_required
class BackendArticleUpdateView(AbsWebView):
    @geass('backend/update.html')
    async def get(self):
        article_id = self.match['id']
        data = await self.redis.get('Article', article_id)
        data['text'] = data['text'].replace('\\r', '\\\\r').replace('\r\n', '\\n').replace('"', '\\"')
        return {'article': data}

    async def post(self):
        data = await self.request.post()
        id = self.match['id']
        new_id = data['id']
        dit = await self.redis.get('Article', id)
        data = dict(dit, **data)

        if data['time'] != '':
            data['created_time'] = data['time']
            data['date'] = todate(data['created_time'], '%b.%d %Y')
        data.pop('time')

        data['html'] = render(data['text'])
        data['updated_time'] = int(str(time.time()).split('.')[0])
        # 分割文章
        data['desc'] = (data['html'])[:(data['html']).find('<hr>', 1)]
        data['desc_text'] = ((data['text'])[:(data['text']).find('-----', 1)]).replace('\n', '').replace('\"', '\'')
        # 删除分割线
        data['html'] = data['html'].replace('<hr>', '', 1)

        if id != new_id:
            await self.redis.delete('Article', id=id)
        await self.redis.set('Article', data, id=new_id)
        # 修改Category
        if dit['category'] != data['category'] or new_id != id:
            await self.redis.ldelete('Category.' + dit['category'], id)
            await self.redis.lpush('Category.' + data['category'], new_id)
        # 修改Archive
        await self.redis.ldelete('Archive', id, isdict=True)
        if ((dit['open'] != data['open'] and dit['open'] is '0') or (data['open'] is '1')) and new_id == id:
            pass
        else:
            await self.redis.lpush('Archive', {
                'id': new_id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)
        # 更新字数统计
        await self.redis.set('Data.WordCount', await word_count(self.redis), many=False)
        return web.HTTPFound('/')


@auth_required
class BackendArticleListView(AbsWebView):
    @geass('backend/articles.html')
    async def get(self):
        data = await self.redis.get_list('Article', isauth=True)
        return {'articles': data}


@auth_required
class BackendProfileView(AbsWebView):
    @geass('backend/profile.html')
    async def get(self):
        data = await self.redis.get('Profile')
        if data is None:
            data = dict(name='', text='', link_desc='')
        if 'link_desc' not in data:
            data['link_desc'] = ''
        return {'profile': {
            'name': data['name'],
            'avatar': '/static/img/avatar.jpg',
            'link_desc': data['link_desc'],
            'text': data['text'].replace('\\r', '\\\\r').replace('\r\n', '\\n').replace('\"', '\\"')
                .replace('<', '&lt;').replace('>', '&gt;')
        }}

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


@auth_required
class BackendConfigView(AbsWebView):
    @geass('backend/config.html')
    async def get(self):
        key = config['admin']['secret_key']
        return {'secret': key,
                'otp_url': otp_url(key, config['admin']['email'], config['admin']['username']),
                'otp': config['admin']['otp'],
                'maintain': config['server']['maintain']}

    async def post(self):
        data = await self.request.post()

        def control(name, group):
            if name in data:
                print(data[name])
                if data[name] == 'open':
                    config[group][name] = True
                elif data[name] == 'close':
                    config[group][name] = False
                merge_config(config)

        control('otp', 'admin')
        control('maintain', 'server')

        return web.json_response({'status': 200})


@auth_required
class BackendLinksView(AbsWebView):
    @geass('backend/link.html')
    async def get(self):
        data = await self.redis.lget('Link', isdict=True, reverse=False)
        if data is None:
            data = []
        return {'friends': data, 'len': len(data) + 1}

    async def post(self):
        data = dict({}, **await self.request.post())
        await self.redis.lpush('Link', data, isdict=True)
        return web.HTTPFound('/manage/links')


@auth_required
class BackendLinksUpdateView(AbsWebView):
    @geass('backend/simple_link.html')
    async def get(self):
        id = self.match['id']
        data = await self.redis.lget('Link', isdict=True)
        if data is None:
            return await http_400_response('Data Error')
        for item in data:
            if item['id'] == id:
                return {'link': item}
        return await http_400_response('Data Error')

    async def post(self):
        data = dict({}, **await self.request.post())
        _id = data['_id']
        data.pop('_id')
        await self.redis.lset('Link', _id, data, isdict=True)
        return web.HTTPFound('/manage/links')

    async def delete(self):
        await self.redis.ldelete('Link', isdict=True)
        return web.json_response({'status': 'success'})


@auth_required
class BackendSecurityView(AbsWebView):
    @geass('backend/security.html')
    async def get(self):
        username = config['admin']['username']
        users = await self.redis.get('Auth.U2F') or {}
        if username in users:
            devices = [json.loads(d) for d in users[username]['_u2f_devices_']]
        else:
            devices = []
        return {
            'u2f': config['admin']['u2f'],
            'devices': devices
        }

    async def post(self):
        data = await self.request.post()

        def control(name, group):
            if name in data:
                print(data[name])
                if data[name] == 'open':
                    config[group][name] = True
                elif data[name] == 'close':
                    config[group][name] = False
                merge_config(config)

        control('u2f', 'admin')
        return web.json_response({'status': 200})


@auth_required
class U2FAuthEnrollView(AbsWebView):
    @geass('public/yubi_auth.html')
    async def get(self):
        username = config['admin']['username']
        users = await self.redis.get('Auth.U2F') or {}
        if username not in users:
            users[username] = {}

        users[username], req = await enroll(users[username])
        await self.redis.set('Auth.U2F', users, many=False)
        return {'request': req}

    async def post(self):
        username = config['admin']['username']
        users = await self.redis.get('Auth.U2F') or {}
        data = dict(await self.request.post())
        data['date'] = todate(str(time.time()), '%b %d,%Y')
        users[username], ok = await bind(users[username], data)
        if ok:
            await self.redis.set('Auth.U2F', users, many=False)
            return web.json_response(json.dumps(True))
        return web.json_response(json.dumps(False))


class U2FAuthVerifyView(AbsWebView):
    @geass('public/yubi_verify.html')
    async def get(self):
        username = config['admin']['username']
        users = await self.redis.get('Auth.U2F') or {}
        try:
            user = users[username]
        except KeyError:
            return await http_400_response('Auth User Not Found')

        users[username], req = await sign(user)
        await self.redis.set('Auth.U2F', users, many=False)
        return {'request': req}

    async def post(self):
        username = config['admin']['username']
        users = await self.redis.get('Auth.U2F') or {}

        users[username], ok = await verify(users[username], dict(await self.request.post()))
        if ok:
            await self.redis.set('Auth.U2F', users, many=False)
            # return backend
            return web.json_response(json.dumps(True))
        return web.json_response(json.dumps(False))

# RSS View
async def rss_view(request):
    item_list = []
    data = await request.app.redis.get_list('Article')
    for item in data:
        rss_item = RSSItem(
            title=item['title'],
            link='https://wind.moe' + request.app.router['article'].url(
                parts={'id': item['id']}
            ),
            description=item['desc'],
            pubDate=todate(item['created_time']),
            content=item['html']
        )
        item_list.append(rss_item)

    rss = RSS(
        title=config['blog']['name'],
        link=config['blog']['link'],
        description=config['blog']['description'],
        items=item_list,
        lastBuildDate=todate(
            (await request.app.redis.get('Article', await request.app.redis.last('Article')))['created_time'])
    )
    data = rss.result()
    return web.Response(body=data.encode(encoding='utf-8'),
                        content_type='text/xml', charset='utf-8')


from u2flib_server.jsapi import DeviceRegistration
from u2flib_server.u2f import (start_register, complete_register,
                               start_authenticate, verify_authenticate)
import json

users = {}
facet = 'https://wind.moe'


class APIHandler:
    # API View
    def __init__(self):
        pass

    async def paginate(self, request):
        need_paginate = request.GET.get('paging')
        # 如果请求的参数里面没有paging=true的话 就返回全部参数
        if need_paginate != 'true':
            data = await request.app.redis.get_list('Article')
            return web.json_response({'articles': data})

        page_size = request.GET.get('limit', None)
        if not page_size:
            return await http_400_response('Parameter limit is required')
        try:
            page_size = int(page_size)
            if page_size < 1:
                return await http_400_response('Invalid limit parameter')
        except (ValueError, TypeError):
            return await http_400_response('Invalid limit parameter')

        data = await request.app.redis.get_list('Article')
        count = len(data)

        page = int(request.GET.get('page', None))
        try:
            left = (page - 1) * page_size
            right = page * page_size
            if left + 1 > count:
                raise InvalidPage
            elif count < right:
                right = count
        except InvalidPage:
            return await http_400_response('Invalid page parameter')

        publish_data = await request.app.redis.lget('Archive', isdict=True)
        keys_array = [i['id'] for i in publish_data]
        keys = [keys_array[i] for i in range(left, right)]
        result = await request.app.redis.get_list('Article', keys=keys)

        return web.json_response({
            'page': page,
            'count': count,
            'limit': page_size,
            'results': result
        })

    @geass('public/yubi_auth.html')
    async def enroll(self, request):
        username = request.GET.get('username', 'user')
        if username not in users:
            users[username] = {}

        user = users[username]
        devices = [DeviceRegistration.wrap(device)
                   for device in user.get('_u2f_devices', [])]
        enroll = start_register(facet, devices)
        user['_u2f_enroll_'] = enroll.json
        res = json.loads(enroll.json)
        return {'request': res['registerRequests'][0]}

    async def bind(self, request):
        username = request.GET.get('username', 'user')
        data = dict(await request.post())
        data = data['tokenResponse']
        user = users[username]
        try:
            binding, cert = complete_register(user.pop('_u2f_enroll_'), data,
                                              [facet])

            devices = [DeviceRegistration.wrap(device)
                       for device in user.get('_u2f_devices_', [])]
            devices.append(binding)

            user['_u2f_devices_'] = [d.json for d in devices]
            #print("U2F device enrolled. Username: %s", username)
            #print("Attestation certificate:\n%s", cert.public_bytes(Encoding.PEM))
        except ValueError:
            return web.json_response(json.dumps(False))
        return web.json_response(json.dumps(True))

    @geass('public/yubi_verify.html')
    async def sign(self, request):
        username = request.GET.get('username', 'user')
        try:
            user = users[username]
        except KeyError:
            return {'request': 'error'}
        devices = [DeviceRegistration.wrap(device)
                   for device in user.get('_u2f_devices_', [])]
        challenge = start_authenticate(devices)
        user['_u2f_challenge_'] = challenge.json
        res = json.loads(challenge.json)
        return {'request': res['authenticateRequests'][0]}

    async def verify(self, request):
        username = request.GET.get('username', 'user')
        user = users[username]
        data = dict(await request.post())
        data = data['tokenResponse']
        devices = [DeviceRegistration.wrap(device)
                   for device in user.get('_u2f_devices_', [])]

        challenge = user.pop('_u2f_challenge_')
        try:
            c, t = verify_authenticate(devices, challenge, data, [facet])
            print(c, t)
        except AttributeError:
            return web.json_response(json.dumps(False))
        return web.json_response(json.dumps(True))