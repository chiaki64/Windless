#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Views

import datetime
import time
import aiohttp_jinja2
import misaka
from aiohttp import web
from aiohttp_auth import auth
from components.rss import RSS, RSSItem
from utils import word_count


class IndexView(web.View):
    @aiohttp_jinja2.template('article/articles.html')
    async def get(self):
        data = await self.request.app.redis.get_list('Article')
        return {'articles': data}


class ArticleListView(web.View):
    @aiohttp_jinja2.template('article/articles.html')
    async def get(self):
        category = self.request.match_info['category'].lower()
        data_list = await self.request.app.redis.lget('Category.' + category)
        data = await self.request.app.redis.get_list('Article', data_list)
        return {'articles': data}


class ArticleView(web.View):
    @aiohttp_jinja2.template('article/article.html')
    async def get(self):
        id = self.request.match_info['id']
        if id.isdigit() is False:
            # Return 400
            pass
        data = await self.request.app.redis.get('Article', id)
        identifier = self.request.app.router['article'].url(
            parts={'id': self.request.match_info['id']}
        )
        return {"article": data, 'PAGE_IDENTIFIER': identifier}


class ArchiveView(web.View):
    # 10-03 Title
    @aiohttp_jinja2.template('static/archive.html')
    async def get(self):
        data = await self.request.app.redis.lget('Archive', isdict=True)
        print(data)
        return {'archive': data}


class LinkView(web.View):
    @aiohttp_jinja2.template('static/links.html')
    async def get(self):
        data = await self.request.app.redis.get_list('Link')
        if data is None:
            data = []
        identifier = self.request.app.router['links'].url()
        return {'friends': data, 'PAGE_IDENTIFIER': identifier}


class ProfileView(web.View):
    @aiohttp_jinja2.template('static/about.html')
    async def get(self):
        words = await self.request.app.redis.get('Data.WordCount')
        return {
            'word_count': words
        }


class BookView(web.View):
    @aiohttp_jinja2.template('static/book.html')
    async def get(self):
        return {}


class LoginView(web.View):
    @aiohttp_jinja2.template('static/login.html')
    async def get(self):
        return {}

    async def post(self):
        data = await self.request.post()
        # _token email otp password remember
        account = await self.request.app.redis.get('User')
        if account['email'] == data['email'] \
                and account['password'] == data['password']:
            await auth.remember(self.request, account['username'])
            return web.HTTPFound('/manage')
        return web.HTTPFound('/auth/login')


@auth.auth_required
class LogoutView(web.View):
    async def get(self):
        await auth.forget(self.request)
        return web.HTTPFound('/')


@auth.auth_required
class BackendIndexView(web.View):
    @aiohttp_jinja2.template('backend/index.html')
    async def get(self):
        return {}


@auth.auth_required
class BackendArticleEditView(web.View):
    @aiohttp_jinja2.template('backend/edit.html')
    async def get(self):
        return {}

    async def post(self):
        data = await self.request.post()
        # important
        data = dict({}, **data)
        data['html'] = misaka.html(data['text'])
        data['created_time'] = time.time()
        data['date'] = time.strftime('%b.%d %Y', time.localtime(data['created_time']))
        id = await self.request.app.redis.set('Article', data)
        # Save to Category
        await self.request.app.redis.lpush('Category.' + data['category'], id)
        # Save to Archive
        if data['open'] is '0':
            await self.request.app.redis.lpush('Archive', {
                'id': id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)
        # 更新字数统计
        await self.request.app.redis.set('Data.WordCount', await word_count(self.request.app.redis), many=False)
        return web.HTTPFound('/')


@auth.auth_required
class BackendArticleUpdateView(web.View):
    @aiohttp_jinja2.template('backend/update.html')
    async def get(self):
        article_id = self.request.match_info['id']
        data = await self.request.app.redis.get('Article', article_id)
        data['text'] = data['text'].replace('\r\n', '\\n')
        return {'article': data}

    async def post(self):
        data = await self.request.post()
        id = self.request.match_info['id']
        dit = await self.request.app.redis.get('Article', id)
        data = dict(dit, **data)
        data['html'] = misaka.html(data['text'])
        data['updated_time'] = time.time()
        await self.request.app.redis.set('Article', data, id=id)
        # Change Category
        if dit['category'] != data['category']:
            await self.request.app.redis.ldelete('Category.' + dit['category'], id)
            await self.request.app.redis.lpush('Category.' + data['category'], id)
        # Change Archive
        await self.request.app.redis.ldelete('Archive', id, isdict=True)
        if (dit['open'] != data['open'] and dit['open'] is '0') or (data['open'] is '1'):
            pass
        else:
            await self.request.app.redis.lpush('Archive', {
                'id': id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)
        # 更新字数统计
        await self.request.app.redis.set('Data.WordCount', await word_count(self.request.app.redis), many=False)
        return web.HTTPFound('/')


@auth.auth_required
class BackendArticleListView(web.View):
    @aiohttp_jinja2.template('backend/articles.html')
    async def get(self):
        data = await self.request.app.redis.get_list('Article', isauth=True)
        return {'articles': data}


@auth.auth_required
class BackendProfileView(web.View):
    @aiohttp_jinja2.template('backend/profile.html')
    async def get(self):
        # TODO
        return {'profile': {
            'name': '稗田千秋',
            'avatar': '/static/img/avatar.jpg'
        }}

    async def post(self):
        data = dict({}, **await self.request.post())

        path = './static/img/avatar.jpg'
        if data['avatar'] != b'':
            # avatar = data['avatar']
            file = open(path, 'wb')
            file.write(data['avatar'].file.read())

        if 'avatar' in data:
            del data['avatar']
        await self.request.app.redis.set('Profile', data)
        return web.HTTPFound('/manage/profile')


@auth.auth_required
class BackendConfigView(web.View):
    @aiohttp_jinja2.template('backend/config.html')
    async def get(self):
        return {}


@auth.auth_required
class BackendLinksView(web.View):
    @aiohttp_jinja2.template('backend/link.html')
    async def get(self):
        data = await self.request.app.redis.lget('Link', isdict=True)
        if data is None:
            data = []
        return {'friends': data}

    async def post(self):
        data = dict({}, **await self.request.post())
        data['id'] = data['name']
        await self.request.app.redis.lpush('Link', data, isdict=True)
        return web.HTTPFound('/manage/links')


# RSS View
async def rss_view(request):
    list = await request.app.redis.count('Article')
    item_list = []
    data = await request.app.redis.get_list('Article')
    for item in data:
        rss_item = RSSItem(
            title=item['title'],
            link='https://wind.moe' + request.app.router['article'].url(
                parts={'id': item['id']}
            ),
            description='None',
            pubDate=datetime.datetime.utcfromtimestamp(item['created_time']),
            content=item['html']
        )
        item_list.append(rss_item)

    # TODO: 从 Profile 获取
    rss = RSS(
        title='Windless',
        link='https://wind.moe',
        description="WindCore 是稗田千秋的一个个人博客,记录个人的点点滴滴,包含随笔,代码,日常,ACGN等内容.",
        items=item_list
    )
    data = rss.result()
    return web.Response(body=data.encode(encoding='utf-8'),
                        content_type='text/xml', charset='utf-8')


# 40x View

class APIHandler:
    # API View
    def __init__(self):
        pass
