#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Route

import views

api_handle = views.APIHandler()

routes = [
    # Article
    ('GET', '/', views.IndexView, 'index'),
    ('GET', '/category/{category}', views.ArticleListView, 'category'),
    ('GET', '/article/{id}', views.ArticleView, 'article'),
    # Static
    ('GET', '/links', views.LinkView, 'links'),
    ('GET', '/archive', views.ArchiveView, 'archive'),
    # ('GET', '/book', views.BookView, 'book'),
    ('GET', '/about', views.ProfileView, 'about'),
    ('GET', '/feed', views.rss_view, 'rss'),
    # Account
    ('*', '/auth/login', views.LoginView, 'login'),
    ('GET', '/auth/logout', views.LogoutView, 'logout'),
    # Backend Route
    ('GET', '/manage/', views.BackendIndexView, '_index'),
    ('GET', '/manage/articles', views.BackendArticleListView, '_articles'),
    ('*', '/manage/article/edit', views.BackendArticleEditView, '_article-edit'),
    ('*', '/manage/article/{id}/edit', views.BackendArticleUpdateView, '_article-update'),
    ('*', '/manage/profile', views.BackendProfileView, '_profile'),
    ('*', '/manage/links', views.BackendLinksView, '_links'),
    ('*', '/manage/link/{id}', views.BackendLinksUpdateView, '_link-update'),
    ('*', '/manage/config', views.BackendConfigView, '_config'),
    # API
    ('GET', '/api/article', api_handle.paginate, 'api_article')
]
