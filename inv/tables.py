#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2021-01-31
@author: Shell.Xu
@copyright: 2021, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import django_tables2 as tables

from .models import InvRec


row_colors = {1: "bg-success", 2: "bg-danger", 3: "bg-info"}


class InvRecTable(tables.Table):

    class Meta:

        model = InvRec
        fields = ('date', 'cat', 'amount', 'price', 'value', 'rate', 'commission')
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table'}
        row_attrs = {
            'class': lambda record: row_colors.get(record.cat)
        }
