#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from io import StringIO


class BaseXML:
    def render(self, out, encoding="utf-8"):
        from xml.sax import saxutils
        handler = saxutils.XMLGenerator(out, encoding=encoding, short_empty_elements=True)
        self.publish(handler)
        handler.endDocument()

    def result(self, encoding="utf-8"):
        f = StringIO()
        self.render(f, encoding)
        return f.getvalue()

    def publish(self, handler):
        pass


def _element(handler, name, obj=None, short=False, attr={}):
    handler._short_empty_elements = short
    if isinstance(obj, str) or obj is None:
        handler.startElement(name, attr)
        if obj is not None:
            handler.characters(obj)
        handler.endElement(name)
    else:
        obj.publish(handler)


def _opt_element(handler, name, obj):
    if obj is None:
        return
    _element(handler, name, obj)


def _format_date(dt):
    return "%s, %02d %s %04d %02d:%02d:%02d GMT+8" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()],
        dt.day,
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1],
        dt.year, dt.hour, dt.minute, dt.second)


class DateElement:
    def __init__(self, name, dt):
        self.name = name
        self.dt = dt

    def publish(self, handler):
        _element(handler, self.name, _format_date(self.dt))


class RSS(BaseXML):
    rss_attr = {'version': '2.0',
                'xmlns:atom': 'http://www.w3.org/2005/Atom'}
    channel_attr = {
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/'
    }

    def __init__(self,
                 title,
                 link,
                 description,
                 language='zh-cn',
                 lastBuildDate=datetime.datetime.now(),

                 items=None
                 ):
        self.title = title
        self.link = link
        self.description = description
        self.language = language
        self.lastBuildDate = lastBuildDate
        self.items = [] if items is None else items

    def publish(self, handler):
        handler.startElement('rss', self.rss_attr)
        handler.startElement('channel', self.channel_attr)

        _element(handler, 'title', self.title)
        _element(handler, "link", self.link)
        _element(handler, "description", self.description)
        _element(handler, "atom:link", short=True, attr={'rel': 'self', 'href': self.link})

        _opt_element(handler, "language", self.language)
        lastBuildDate = self.lastBuildDate
        if isinstance(lastBuildDate, datetime.datetime):
            lastBuildDate = DateElement("lastBuildDate", lastBuildDate)
        _opt_element(handler, "lastBuildDate", lastBuildDate)

        for item in self.items:
            item.publish(handler)

        handler.endElement("channel")
        handler.endElement("rss")
        # print(handler)


class RSSItem(BaseXML):
    item_attr = {}

    def __init__(self,
                 title,
                 link,
                 content,
                 description="暂无简介，请看原文",
                 author=None,
                 pubDate=None):
        self.title = title
        self.link = link
        self.content = content
        self.description = description
        self.author = author
        self.guid = self.link
        self.pubDate = pubDate

    def publish(self, handler):
        handler.startElement('item', self.item_attr)

        _opt_element(handler, "title", self.title)
        _opt_element(handler, "author", self.author)
        _opt_element(handler, "link", self.link)
        _opt_element(handler, "description", self.description)
        _opt_element(handler, "content:encoded", self.content)

        _opt_element(handler, "guid", self.guid)
        pubDate = self.pubDate
        if isinstance(pubDate, datetime.datetime):
            pubDate = DateElement("pubDate", pubDate)
        _opt_element(handler, "pubDate", pubDate)

        handler.endElement("item")


if __name__ == '__main__':
    from xml.sax import saxutils
    RSS('1', '3', '2').publish(saxutils.XMLGenerator())
