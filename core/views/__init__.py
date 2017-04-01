#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
from components.eternity import config
from components.rss import RSS, RSSItem
from utils.period import todate

__all__ = ['backend', 'public', 'auth']


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
        title=config.rss['name'],
        link=config.rss['link'],
        description=config.rss['description'],
        items=item_list,
        lastBuildDate=todate(
            (await request.app.redis.get('Article', await request.app.redis.last('Article')))['created_time'])
    )
    data = rss.result()
    return web.Response(body=data.encode(encoding='utf-8'),
                        content_type='text/xml', charset='utf-8')
