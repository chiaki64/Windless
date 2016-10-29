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
from utils import word_count, load_config

config = load_config()


class AbsWebView(web.View):
    def __init__(self, request):
        super(AbsWebView, self).__init__(request)
        self.redis = self.request.app.redis


class IndexView(AbsWebView):
    @aiohttp_jinja2.template('article/articles.html')
    async def get(self):
        data = await self.redis.get_list('Article')
        return {'articles': data}


class ArticleListView(AbsWebView):
    @aiohttp_jinja2.template('article/articles.html')
    async def get(self):
        category = self.request.match_info['category'].lower()
        data_list = await self.redis.lget('Category.' + category)
        data = await self.redis.get_list('Article', data_list)
        return {'articles': data}


class ArticleView(AbsWebView):
    @aiohttp_jinja2.template('article/article.html')
    async def get(self):
        id = self.request.match_info['id']
        if id.isdigit() is False:
            return web.HTTPNotFound()
        data = await self.redis.get('Article', id)
        if data is None:
            return web.HTTPNotFound()
        identifier = self.request.app.router['article'].url(
            parts={'id': self.request.match_info['id']}
        )
        return {"article": data, 'PAGE_IDENTIFIER': identifier}


class ArchiveView(AbsWebView):
    # 10-03 Title
    @aiohttp_jinja2.template('static/archive.html')
    async def get(self):
        data = await self.redis.lget('Archive', isdict=True)
        dit = {}
        for i in data:
            date = time.strftime('%Y年%m月|%d日', time.localtime(i['created_time']))
            month = date.split('|')[0]
            if month not in dit:
                dit[month] = []
            i['day'] = date.split('|')[1]
            dit[month].append(i)
        print(dit)
        return {'archive': dit,
                'profile': await self.redis.get('Profile')}


class LinkView(AbsWebView):
    @aiohttp_jinja2.template('static/links.html')
    async def get(self):
        data = await self.redis.lget('Link', isdict=True)
        print(data)
        if data is None:
            data = []
        identifier = self.request.app.router['links'].url()
        return {'friends': data, 'PAGE_IDENTIFIER': identifier}


class ProfileView(AbsWebView):
    @aiohttp_jinja2.template('static/about.html')
    async def get(self):
        data = await self.redis.get('Profile')
        words = await self.redis.get('Data.WordCount')
        return {
            'profile': data,
            'word_count': words
        }


# class BookView(AbsWebView):
#    @aiohttp_jinja2.template('static/book.html')
#    async def get(self):
#        pass


class LoginView(AbsWebView):
    @aiohttp_jinja2.template('static/login.html')
    async def get(self):
        pass

    async def post(self):
        data = await self.request.post()
        # _token email otp password remember
        account = await self.redis.get('User')
        if account['email'] == data['email'] \
                and account['password'] == data['password']:
            await auth.remember(self.request, account['username'])
            return web.HTTPFound('/manage')
        return web.HTTPFound('/auth/login')


@auth.auth_required
class LogoutView(AbsWebView):
    async def get(self):
        await auth.forget(self.request)
        return web.HTTPFound('/')


@auth.auth_required
class BackendIndexView(AbsWebView):
    @aiohttp_jinja2.template('backend/index.html')
    async def get(self):
        # 数据监控 服务器数据、文章情况等
        import psutil
        import platform
        system = platform.uname().system
        release = platform.uname().release
        cpu_used = psutil.cpu_percent()
        memory_used = psutil.virtual_memory().percent

        article_count = await self.redis.count('Article')
        publish_count = (await self.redis.get('Archive'))['list'].__len__()
        category = ['algorithm', 'acgn', 'code', 'daily', 'essay', 'web']
        category_count = {}
        for cat in category:
            category_count[cat] = (await self.redis.lget('Category.' + cat)).__len__()

        print(category_count)
        return {
            'system': {
                'version': system,
                'release': release,
                'cpu_used': cpu_used,
                'memory_used': memory_used
            },
            'articles': {
                'count': article_count,
                'publish': publish_count,
                'category': category_count
            }
        }


@auth.auth_required
class BackendArticleEditView(AbsWebView):
    @aiohttp_jinja2.template('backend/edit.html')
    async def get(self):
        pass

    async def post(self):
        data = await self.request.post()
        # important
        data = dict({}, **data)
        # 处理迁移文章
        if data['id'] == '':
            data['id'] = None

        data['html'] = misaka.html(data['text'])
        data['created_time'] = time.time()

        if data['time'] == '':
            data['date'] = time.strftime('%b.%d %Y', time.localtime(data['created_time']))
        else:
            data['date'] = time.strftime('%b.%d %Y', time.localtime(int(data['time'].strip())))
        # 分割文章
        data['desc'] = (data['html'])[:(data['html']).find('<hr>', 1)]
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
        return web.HTTPFound('/')


@auth.auth_required
class BackendArticleUpdateView(AbsWebView):
    @aiohttp_jinja2.template('backend/update.html')
    async def get(self):
        article_id = self.request.match_info['id']
        data = await self.redis.get('Article', article_id)
        print(data['text'])

        data['text'] = data['text'].replace('\\r', '\\\\r').replace('\r\n', '\\n')
        return {'article': data}

    async def post(self):
        data = await self.request.post()
        id = self.request.match_info['id']
        dit = await self.redis.get('Article', id)
        data = dict(dit, **data)
        data['html'] = misaka.html(data['text'])
        data['updated_time'] = time.time()
        # 分割文章
        data['desc'] = (data['html'])[:(data['html']).find('<hr>', 1)]
        # 删除分割线
        data['html'] = data['html'].replace('<hr>', '', 1)
        await self.redis.set('Article', data, id=id)
        # 修改Category
        if dit['category'] != data['category']:
            await self.redis.ldelete('Category.' + dit['category'], id)
            await self.redis.lpush('Category.' + data['category'], id)
        # 修改Archive
        await self.redis.ldelete('Archive', id, isdict=True)
        if (dit['open'] != data['open'] and dit['open'] is '0') or (data['open'] is '1'):
            pass
        else:
            await self.redis.lpush('Archive', {
                'id': id,
                'title': data['title'],
                'category': data['category'],
                'created_time': data['created_time']
            }, isdict=True)
        # 更新字数统计
        await self.redis.set('Data.WordCount', await word_count(self.redis), many=False)
        return web.HTTPFound('/')


@auth.auth_required
class BackendArticleListView(AbsWebView):
    @aiohttp_jinja2.template('backend/articles.html')
    async def get(self):
        data = await self.redis.get_list('Article', isauth=True)
        return {'articles': data}


@auth.auth_required
class BackendProfileView(AbsWebView):
    @aiohttp_jinja2.template('backend/profile.html')
    async def get(self):
        data = await self.redis.get('Profile')
        if data is None:
            data = dict(name='', text='')
        return {'profile': {
            'name': data['name'],
            'avatar': '/static/img/avatar.jpg',
            'text': data['text'].replace('\r\n', '\\n')
        }}

    async def post(self):
        data = dict({}, **await self.request.post())
        data['html'] = misaka.html(data['text'])
        path = './static/img/avatar.jpg'
        if data['avatar'] != b'':
            file = open(path, 'wb')
            file.write(data['avatar'].file.read())

        if 'avatar' in data:
            del data['avatar']
        data['updated_date'] = time.strftime('%b.%d %Y', time.localtime())
        await self.redis.set('Profile', data, many=False)
        return web.HTTPFound('/manage/profile')


@auth.auth_required
class BackendConfigView(AbsWebView):
    @aiohttp_jinja2.template('backend/config.html')
    async def get(self):
        pass


@auth.auth_required
class BackendLinksView(AbsWebView):
    @aiohttp_jinja2.template('backend/link.html')
    async def get(self):
        data = await self.redis.lget('Link', isdict=True)
        if data is None:
            data = []
        return {'friends': data}

    async def post(self):
        data = dict({}, **await self.request.post())
        data['id'] = data['name']
        await self.redis.lpush('Link', data, isdict=True)
        return web.HTTPFound('/manage/links')


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
            pubDate=datetime.datetime.fromtimestamp(item['created_time']),
            content=item['html']
        )
        item_list.append(rss_item)

    rss = RSS(
        title=config['blog']['name'],
        link=config['blog']['link'],
        description=config['blog']['description'],
        items=item_list,
        lastBuildDate=datetime.datetime.fromtimestamp(
            (await request.app.redis.get('Article', await request.app.redis.last('Article')))['created_time'])
    )
    data = rss.result()
    return web.Response(body=data.encode(encoding='utf-8'),
                        content_type='text/xml', charset='utf-8')


class APIHandler:
    # API View
    def __init__(self):
        pass

    def index(self):
        pass

    def category(self):
        pass

    def article(self):
        pass
