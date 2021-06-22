#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2021-02-05
@author: Shell.Xu
@copyright: 2021, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
from __future__ import unicode_literals
import json

from django.conf import settings
import requests
import investpy
from bs4 import BeautifulSoup


no_proxies = {
    "http": "",
    "https": "",
}

def CoinGecko(_id):
    from pycoingecko import CoinGeckoAPI
    cg = CoinGeckoAPI()
    return cg.get_price(ids=_id, vs_currencies='usd')[_id]['usd']


def SGE(_id):
    resp = requests.get('https://www.sge.com.cn/sjzx/yshqbg', proxies=no_proxies)
    doc = BeautifulSoup(resp.content, 'lxml')
    for tr in doc.select('div.memberName tr.border_ea'):
        data = [td.get_text() for td in tr.select('td')]
        if data[0] == _id:
            return data[1]


def EastmoneyFund(_id):
    resp = requests.get(f'http://fund.eastmoney.com/{_id}.html', proxies=no_proxies)
    doc = BeautifulSoup(resp.content, 'lxml')
    for span in doc.select('span.fix_dwjz'):
        return span.get_text()


def SinaFin(_id):
    # 股票名称、今日开盘价、昨日收盘价、当前价格、今日最高价、今日最低价、竞买价、竞卖价
    # 成交股数、成交金额、买1手、买1报价、买2手、买2报价、…、买5报价、…、卖5报价、日期、时间
    resp = requests.get(f'http://hq.sinajs.cn/list={_id}', proxies=no_proxies)
    return resp.text.split('"')[1].split(',')[3]


def InvestingFund(_id):
    try:
        obj = json.loads(_id)
    except ValueError:
        return
    if hasattr(obj, 'items'):
        df = investpy.get_fund_recent_data(**obj)
    elif hasattr(obj, '__iter__'):
        df = investpy.get_fund_recent_data(*obj)
    return df.iloc[-1].Close


def InvestingCurrency(_id):
    df = investpy.get_currency_cross_recent_data(
        currency_cross=f'{_id}/CNY')
    if not df.empty:
        return df.iloc[-1].Close
