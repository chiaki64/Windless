#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import views
from components.eternity import config
from views import *

routes = {
    'Main': {
        'prefix': '',
        'url': {
            'GET': [
                ('/', public.IndexView, 'index'),
                ('/category/{category}', public.ListView, 'category'),
                ('/article/{id}', public.ArticleView, 'article'),
                ('/links', public.LinkView, 'links'),
                ('/archive', public.ArchiveView, 'archive'),
                ('/about', public.ProfileView, 'about'),
                ('/feed', views.rss_view, 'rss'),
                ('/guest-book', public.GuestBookView, 'guest-book'),
                ('/tag/{tag}', public.TagView, 'tag')
            ],
            '*': [
                ('/disqus', public.CommentView, 'comment')
            ]
        }
    },
    'Auth': {
        'prefix': '/auth',
        'url': {
            'GET': [
                ('/logout', auth.LogoutView, 'logout'),
                ('/enroll', auth.EnrollView, 'u2f_enroll')
            ],
            'POST': [
                ('/bind', auth.EnrollView, 'u2f_bind')
            ],
            '*': [
                ('/login', auth.LoginView, 'login')
            ]
        }
    },
    'Admin': {
        'prefix': '/manage',
        'url': {
            'GET': [
                ('', backend.IndexView, '_index'),
                ('/articles', backend.ArticleListView, '_articles')
            ],
            '*': [
                ('/article/edit', backend.ArticleEditView, '_article-edit'),
                ('/article/{id}/edit', backend.ArticleUpdateView, '_article-update'),
                ('/config', backend.ConfigView, '_config'),
                ('/profile', backend.ProfileView, '_profile'),
                ('/links', backend.LinksView, '_links'),
                # ('/link/{id}', backend.LinksUpdateView, '_link-update'),
                ('/security', backend.SecurityView, '_security'),
                ('/guest-book', backend.GuestBookView, '_guest-book')
            ]
        }
    }
}


async def compass(router):
    for item in routes:
        for method in routes[item]['url']:
            for route in routes[item]['url'][method]:
                router.add_route(method, routes[item]['prefix'] + route[0], route[1], name=route[2])

    if config.dev:
        router.add_static('/static/',
                          path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../resource/static'),
                          name='static')
