#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from utils.period import todate
from utils.shortcut import (rebuild_html,
                            render)


class Serializer:
    # 一定要传form={}进来
    def __init__(self, **kwargs):
        self.data = self.serialize(kwargs.get('form'))
        self.exclude = ()
        self.is_valid()

    def serialize(self, dit):
        return dit

    def is_valid(self):
        for key in self.data:
            if self.data[key] is None and key not in self.exclude:
                # print('invalid')
                return False
        # print('valid')
        return True


class ArticleSer(Serializer):
    def __init__(self, **kwargs):
        super(ArticleSer, self).__init__(**kwargs)
        self.exclude = ('id', 'updated_date', 'pic_address', 'axis_y', 'desc', 'citation')

    def serialize(self, form):
        # TODO:考虑更新和创建
        form['created_time'] = (str(int(time.time())) if form['time'] == '' else form['time'])
        if form.get('edit'):
            form['updated_time'] = form['created_time']
        if form.get('update') == 'on':
            form['updated_time'] = str(int(time.time()))

        form['html'], form['desc'] = rebuild_html(render(form['text']))

        return dict(
            id=None if form.get('id') == '' else form.get('id'),
            created_time=form.get('created_time'),
            updated_time=form.get('updated_time'),
            date=todate(form['created_time'], '%b.%d %Y'),  # form.get('date') or
            # updated_date=form.get('updated_date') or todate(form['updated_time'], '%b.%d %Y %H:%M:%S'),
            title=form.get('title'),
            tag=form.get('tag'),
            author=form.get('author'),
            category=form.get('category'),
            text=form.get('text'),
            html=form['html'],
            desc=form['desc'],
            desc_text=((form.get('text'))[:(form.get('text')).find('-----', 1)]).replace('\n', ' ').replace('\"', '\''),
            citation=form.get('citation'),
            top=form.get('top'),
            open=form.get('open'),
            pic=form.get('pic'),
            pic_address=form.get('pic_address'),
            axis_y=form.get('axis_y'),
            comments=form.get('comments') or []
        )


class ArchiveSer(Serializer):
    def __init__(self, **kwargs):
        super(ArchiveSer, self).__init__(**kwargs)
        self.exclude = ()

    def serialize(self, form):

        return dict(
            id=form.get('id'),
            title=form.get('title'),
            category=form.get('category'),
            created_time=form.get('created_time'),
        )


class LinkSer(Serializer):
    def __init__(self, **kwargs):
        super(LinkSer, self).__init__(**kwargs)
        self.exclude = ()

    def serialize(self, form):
        return dict()


class ConfigSer(Serializer):
    def __init__(self, **kwargs):
        super(ConfigSer, self).__init__(**kwargs)
        self.exclude = ()

    def serialize(self, form):
        return dict()

