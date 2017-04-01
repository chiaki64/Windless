#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


class Singleton(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
            return cls._instance
        else:
            return cls._instance


class AbsWebView(web.View):
    def __init__(self, request):
        super(AbsWebView, self).__init__(request)
        self.redis = self.request.app.redis
        self._get = self.request.GET.get
        self.match = self.request.match_info
