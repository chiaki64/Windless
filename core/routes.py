#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Route

import views

api_handle = views.APIHandler()

routes = {
    'Home': {
        'prefix': '',
        'data': {
            'GET': [
                ('/', views.IndexView, 'index'),
                ('/category/{category}', views.ArticleListView, 'category'),
                ('/article/{id}', views.ArticleView, 'article'),
                ('/links', views.LinkView, 'links'),
                ('/archive', views.ArchiveView, 'archive'),
                ('/about', views.ProfileView, 'about'),
                ('/feed', views.rss_view, 'rss')
            ]
        }
    },
    'Auth': {
        'prefix': '/auth',
        'data': {
            'GET': [
                ('/logout', views.LogoutView, 'logout'),
                ('/enroll', views.U2FAuthEnrollView, 'u2f_enroll'),
                # ('/sign', views.U2FAuthVerifyView, 'u2f_sign')
            ], 'POST': [
                ('/bind', views.U2FAuthEnrollView, 'u2f_bind'),
                # ('/verify', views.U2FAuthVerifyView, 'u2f_verify')
            ], '*': [
                ('/login', views.LoginView, 'login')

            ]
        }
    },
    'Admin': {
        'prefix': '/manage',
        'data': {
            'GET': [
                ('', views.BackendIndexView, '_index'),
                ('/articles', views.BackendArticleListView, '_articles')
            ],
            '*': [
                ('/article/edit', views.BackendArticleEditView, '_article-edit'),
                ('/article/{id}/edit', views.BackendArticleUpdateView, '_article-update'),
                ('/profile', views.BackendProfileView, '_profile'),
                ('/links', views.BackendLinksView, '_links'),
                ('/link/{id}', views.BackendLinksUpdateView, '_link-update'),
                ('/config', views.BackendConfigView, '_config'),
                ('/security', views.BackendSecurityView, '_security')
            ]
        }
    },
    'API': {
        'prefix': '/api',
        'data': {
            'GET': [
                ('/article', api_handle.paginate, 'api_article'),
                # ('/enroll', api_handle.enroll, 'api_enroll'),
                # ('/sign', api_handle.sign, 'api_sign')
            ],
            'POST': [
                # ('/bind', api_handle.bind, 'api_bind'),
                # ('/verify', api_handle.verify, 'api_verify')
            ]
        }
    }
}
