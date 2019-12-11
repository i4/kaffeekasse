# SPDX-License-Identifier: GPL-3.0-or-later

import django.contrib.auth.views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('buy', views.buy, name='buy'),
    path('buy_revert', views.buy_revert, name='buy_revert'),
    path('transfer', views.transfer, name='transfer'),
    path('transfer_revert', views.transfer_revert, name='transfer_revert'),
    path('charge', views.charge, name='charge'),
    path('charge_revert', views.charge_revert, name='charge_revert'),

    # Auth
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),

    path('password_login',
        django.contrib.auth.views.LoginView.as_view(template_name='admin/login.html'),
        name='password_login'),
]
