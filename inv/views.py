#!/usr/bin/python
# -*- coding: utf-8 -*-
import decimal
import datetime

import pandas as pd
from scipy.optimize import fsolve

from django.http import HttpResponse
from django.shortcuts import render

from .models import Currency, Category, Bank, Account, AccountCategory, AccountRec, Risk, InvProj, InvRec
from . import tables


def proj_stat(request, projid):
    proj = InvProj.objects.get(id=int(projid))
    tab = tables.InvRecTable(proj.invrec_set.all(), request=request)
    env = {
        'proj': proj,
        'table': tab,
    }
    return render(request, 'inv/proj_stat.html', env)


def add_vectory(a, b):
    return [i+j for i, j in zip(a, b)]


def sub_vectory(a, b):
    return [i-j for i, j in zip(a, b)]


def div_vectory(a, b):
    return [i/j for i, j in zip(a, b) if j != 0]


def balance_sheet(request):
    curs = Currency.objects.all()
    sheet = {}
    for cat in Category.objects.all():
        values = cat.values_by_currency()
        l = []
        total = 0
        for cur in curs:
            l.append(values.get(cur.name, decimal.Decimal()))
            total += values.get(cur.name, decimal.Decimal()) * cur.rate
        l.append(total)
        sheet.setdefault(cat.cat, [])
        sheet[cat.cat].append((cat, l))

    assets = [decimal.Decimal(),]*(len(curs)+1)
    liabilities = [decimal.Decimal(),]*(len(curs)+1)
    for i in range(1, 6):
        sums = [decimal.Decimal(),]*(len(curs)+1)
        for name, values in sheet[i]:
            sums = add_vectory(sums, values)
        if i == 1:
            current_asset = sums[:]
        if i == 2:
            current_liabilities = sums[:]
        if i in {1, 3, 5}:
            assets = add_vectory(assets, sums)
        else:
            liabilities = add_vectory(liabilities, sums)
        sheet[i].append(({'name': '小记'}, sums))

    liquidity_list = div_vectory(map(float, current_asset),
                                 map(float, current_liabilities))
    if liquidity_list:
        liquidity_ratio = min(liquidity_list)
    else:
        liquidity_ratio = -1
    debt_asset_ratio = max(div_vectory(map(float, liabilities),
                                       map(float, assets)))

    env = {
        'sheet': sheet,
        'curs': curs,
        'assets': assets,
        'liabilities': liabilities,
        'equity': list(sub_vectory(assets, liabilities)),
        'liquidity_ratio': liquidity_ratio,
        'debt_asset_ratio': 100*debt_asset_ratio,
    }
    return render(request, 'inv/balance_sheet.html', env)


def income_outgoing_sheet(request):
    lastyear = datetime.date.today()-datetime.timedelta(days=365)
    td = datetime.date.today()

    income = []
    for cat in AccountCategory.objects.filter(cat=1).all():
        num = sum((rec.value for rec in cat.accountrec_set.filter(date__gte=lastyear).all()))
        if num:
            income.append((cat.name, num))
    s_income = sum((n for c, n in income))
    income.append(('小计', s_income))

    outgoing = []
    for cat in AccountCategory.objects.filter(cat=2).all():
        num = sum((rec.value for rec in cat.accountrec_set.filter(date__gte=lastyear).all()))
        if num:
            outgoing.append((cat.name, num))
    s_outgoing = sum((n for c, n in outgoing))
    outgoing.append(('小计', s_outgoing))

    investments = []
    iotab = []
    for cat in Category.objects.filter(cat=5).all():
        num = 0
        for proj in cat.invproj_set.filter(isopen=False, end__gte=lastyear).all():
            num -= (proj.value*proj.acct.currency.rate).quantize(decimal.Decimal('1.00'))
            iotab.extend(proj.calc_iotab(td, True))
        if num:
            investments.append((cat.name, num))
    s_investments = sum((n for c, n in investments))
    investments.append(('小计', s_investments))

    def f(r):
        return sum((value*r**dur for dur, value in iotab))
    r = fsolve(f, 1.01)[0]

    env = {
        'income': income,
        'outgoing': outgoing,
        'investments': investments,
        'total_income': s_income+s_investments,
        'total_outgoing': s_outgoing,
        'net_income': s_income+s_investments-s_outgoing,
        'saving_rate': 100*(s_income+s_investments-s_outgoing)/(s_income+s_investments),
        'invest_income_rate': 100*s_investments/(s_income+s_investments),
        'invest_outgoing_rate': 100*s_investments/s_outgoing,
        'invest_rate': 365*100*(r-1),
    }
    return render(request, 'inv/ios.html', env)


def income_details(request):
    df = pd.DataFrame()

    for cat in AccountCategory.objects.filter(cat=1).all():
        s = pd.Series(name=cat.name)
        for rec in cat.accountrec_set.all():
            dt = rec.date.replace(day=1)
            if dt not in s:
                s[dt] = rec.value
            else:
                s[dt] += rec.value
        if s.count():
            df = df.join(s, how='outer')

    for cat in Category.objects.filter(cat=5).all():
        s = pd.Series(name=cat.name)
        for proj in cat.invproj_set.filter(isopen=False).all():
            dt = proj.end.replace(day=1)
            value = (proj.value*proj.acct.currency.rate).quantize(decimal.Decimal('1.00'))
            if dt not in s:
                s[dt] = -value
            else:
                s[dt] += -value
        if s.count():
            df = df.join(s, how='outer')

    df = df.sort_index()
    df['总计'] = df.sum(axis=1)
    env = {
        'title': '收入细节表',
        'code': df.to_html(border=0, classes='table table-striped table-responsive'),
    }
    return render(request, 'inv/raw.html', env)


def outgoing_details(request):
    df = pd.DataFrame()

    for cat in AccountCategory.objects.filter(cat=2).all():
        s = pd.Series(name=cat.name)
        for rec in cat.accountrec_set.all():
            dt = rec.date.replace(day=1)
            if dt not in s:
                s[dt] = rec.value
            else:
                s[dt] += rec.value
        if s.count():
            df = df.join(s, how='outer')
    
    df = df.sort_index()
    df['总计'] = df.sum(axis=1)
    env = {
        'title': '支出细节表',
        'code': df.to_html(border=0, classes='table table-striped table-responsive'),
    }
    return render(request, 'inv/raw.html', env)
