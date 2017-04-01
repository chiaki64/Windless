#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from aiohttp import web
from components.eternity import config
from utils.abstract import AbsWebView
from utils.period import todate
from utils.shortcut import paginate, render
from utils.response import geass, http_400_response


class IndexView(AbsWebView):
    async def get(self):
        page = self._get('page', None)

        # 处理置顶 TODO:储存在变量中 初始化时加载
        if page == 'full':
            # Return all articles
            data = await self.redis.get_list('Article', istop=True)
        else:
            key = self._get('search', None)
            if key is None:
                if page is None:
                    page = 1
                status = await paginate(self.request, page=page, istop=True)
                if status['exit'] == 0:
                    data = status['data']
                else:
                    return await http_400_response(self.request)
                return geass({
                    'articles': data,
                    'page': int(page),
                    'total': status['total']
                }, self.request, 'public/catalog.html')
            else:
                data = []
                result = await self.redis.get_list('Article')
                for item in result:
                    if re.search(key, item['text']) or re.search(key, item['title']) or re.search(key, item['tags']):
                        data.append(item)
        return geass({
            'articles': data,
            'page': 1,
            'total': 1
        }, self.request, 'public/catalog.html')


class ListView(AbsWebView):
    async def get(self):
        page = self._get('page', None)
        category = self.match['category'].lower()
        data_list = await self.redis.lget('Category.' + category)

        if page == 'full':
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
                return await http_400_response(self.request)
            return geass({
                'articles': data,
                'page': int(page),
                'total': status['total'],
                'category': category
            }, self.request, 'public/catalog.html')
        return geass({
            'articles': data,
            'page': 1
        }, self.request, 'public/catalog.html')


class ArticleView(AbsWebView):
    async def get(self):
        id = self.match['id']
        if id.isdigit() is False:
            raise web.HTTPNotFound()
        data = await self.redis.get('Article', id)
        if data is None:
            raise web.HTTPNotFound()

        # 处理时间
        data['created_date'] = todate(data['created_time'], '%Y-%m-%d %H:%M:%S')
        data['updated_date'] = todate(data['updated_time'], '%Y-%m-%d %H:%M:%S')
        # 引用
        data['citations'] = [render(item)[3:-5] for item in data.get('citation').split('|')]
        data['tags'] = [item for item in data.get('tag').split('|')]

        if len(re.findall('[$]{1,2}', data['text'])) > 0:
            math = True
        else:
            math = False
        return geass({
            'article': data,
            'math': math,
            'PAGE_IDENTIFIER': self.request.app.router['article'].url(
                parts={'id': id}
            ),
            'dev': not config.dev,
            'comment': True
        }, self.request, 'public/article.html')


class ArchiveView(AbsWebView):
    async def get(self):
        data = await self.redis.lget('Archive', isdict=True, reverse=True)
        dit = {}
        data.sort(key=lambda x: int(x['created_time']), reverse=True)

        for idx, item in enumerate(data):
            date = todate(item['created_time'], '%Y年|%m月')
            year, month = date.split('|')

            if year not in dit:
                dit[year] = {}
            if month not in dit[year]:
                dit[year][month] = {
                    'length': 0,
                    'post': [],
                    'open': True if idx < 6 else False
                }

            item['date'] = todate(item['created_time'], '%b.%d %Y')
            dit[year][month]['length'] += 1
            dit[year][month]['post'].append(item)
        return geass({
            'archive': dit,
            'profile': await self.redis.get('Profile'),
            'identifier': 'archive'
        }, self.request, 'public/archive.html')


class LinkView(AbsWebView):
    async def get(self):
        value = await self.redis.lget('Link', isdict=True, reverse=False)
        profile = await self.redis.get('Profile')
        data = []
        if value is not None:
            for link in value:
                if link['hide'] != 'true':
                    data.append(link)
        return geass({
            'friends': data,
            'blog': {
                'name': profile['name'],
                'link': config.rss['link'],
                'desc': (await self.redis.get('Profile'))['link_desc']
            },
            'identifier': 'links',
            'comment': True
        }, self.request, 'public/links.html')


class ProfileView(AbsWebView):
    async def get(self):
        data = await self.redis.get('Profile')
        words = await self.redis.get('Data.WordCount')
        return geass({
            'profile': data,
            'word_count': words,
            'identifier': 'about',
            'comment': True
        }, self.request, 'public/about.html')


class GuestBookView(AbsWebView):
    async def get(self):
        data = await self.redis.lget('GuestBook', isdict=True, reverse=True)
        if data is None:
            data = []
        return geass({
            'notes': data,
            'identifier': 'guest-book',
            'comment': True
        }, self.request, 'public/guestbook.html')


class CommentView(AbsWebView):
    async def get(self):
        return geass({
            'host': config.comment['host']
        }, self.request, 'public/comment.html')


class TagView(AbsWebView):
    async def get(self):
        tag = self.match['tag'].lower()
        data = await self.redis.get_list('Article')
        articles = []
        for article in data:
            if tag in [item.lower() for item in article.get('tag').split('|')]:
                articles.append(article)
        return geass({
            'articles': articles,
            'page': 1
        }, self.request, 'public/catalog.html')
