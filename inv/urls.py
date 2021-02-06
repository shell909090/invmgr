#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2021-01-31
@author: Shell.Xu
@copyright: 2021, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from django.conf.urls import url

from . import views


app_name = 'inv'

urlpatterns = [
    url(r'st/(?P<projid>[0-9]+)',
        views.proj_stat, name='proj_stat'),
    url(r'bal',
        views.balance_sheet, name='balance_sheet'),
    url(r'ios',
        views.income_outgoing_sheet, name='income_outgoing_sheet'),
    url(r'ind',
        views.income_details, name='income_details'),
    url(r'ogd',
        views.outgoing_details, name='outgoing_details'),
]
