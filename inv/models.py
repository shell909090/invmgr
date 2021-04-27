#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import decimal
import datetime

from scipy.optimize import fsolve

from django.db import models
from django.urls import reverse
from django.utils.html import format_html


class Currency(models.Model):

    class Meta:
        verbose_name = '币种'
        verbose_name_plural = '币种'

    name = models.CharField('货币名称', max_length=20)
    rate = models.DecimalField('汇率', max_digits=12, decimal_places=4)

    def __str__(self):
        return self.name

    def update_current_price(self):
        if self.name == 'CNY':
            return
        from . import drivers
        price = drivers.InvestingCurrency(self.name)
        if price:
            self.rate = decimal.Decimal(price)
            self.save()


class Category(models.Model):

    class Meta:
        verbose_name = '类别'
        verbose_name_plural = '类别'

    CAT_CHOICES = (
        (1, '流动资产'),
        (2, '流动负债'),
        (3, '固定资产'),
        (4, '长期负债'),
        (5, '投资'),
    )

    name = models.CharField('名称', max_length=20)
    cat = models.IntegerField('类别', choices=CAT_CHOICES)
    driver = models.CharField('数据驱动', max_length=40, blank=True, null=True)

    def __str__(self):
        return self.name

    def values_by_currency(self):
        values = {}
        for a in self.account_set.all():
            values[a.currency.name] = a.value + values.get(a.currency.name, 0)
        for p in self.invproj_set.filter(isopen=True).all():
            values[p.acct.currency.name] = p.value + values.get(p.acct.currency.name, 0)
        return values
        

class Bank(models.Model):

    class Meta:
        verbose_name = '银行'
        verbose_name_plural = '银行'

    name = models.CharField('名称', max_length=20)

    def __str__(self):
        return self.name


class Account(models.Model):

    class Meta:
        verbose_name = '账户'
        verbose_name_plural = '账户'

    bank = models.ForeignKey(Bank, verbose_name='银行', on_delete=models.PROTECT)
    name = models.CharField('名称', max_length=20)
    currency = models.ForeignKey(Currency, verbose_name='币种',
                                 on_delete=models.PROTECT)
    cat = models.ForeignKey(Category, verbose_name='类别', on_delete=models.PROTECT)
    value = models.DecimalField('余额', max_digits=16, decimal_places=2)

    def __str__(self):
        return f'{self.bank.name}-{self.name}'


class AccountCategory(models.Model):

    class Meta:
        verbose_name = '账户收支类别'
        verbose_name_plural = '账户收支类别'

    CAT_CHOICES = (
        (1, '收入'),
        (2, '支出'),
    )

    name = models.CharField('名称', max_length=20)
    cat = models.IntegerField('收支', choices=CAT_CHOICES)

    def __str__(self):
        return self.name


class AccountRec(models.Model):

    class Meta:
        verbose_name = '账户收支'
        verbose_name_plural = '账户收支'

    acct = models.ForeignKey(Account, verbose_name='账户',
                             on_delete=models.PROTECT, blank=True, null=True)
    date = models.DateField('日期')
    cat = models.ForeignKey(AccountCategory, verbose_name='账户收支类别',
                            on_delete=models.PROTECT)
    value = models.DecimalField('金额', max_digits=16, decimal_places=2)
    comment = models.CharField('注释', max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.acct}({self.date})'


class Risk(models.Model):

    class Meta:
        verbose_name = '风险级别'
        verbose_name_plural = '风险级别'

    name = models.CharField('名称', max_length=20)

    def __str__(self):
        return self.name


class InvProj(models.Model):

    class Meta:
        verbose_name = '投资项目'
        verbose_name_plural = '投资项目'

    name = models.CharField('名称', max_length=100)
    code = models.CharField('代码', max_length=50, blank=True, null=True)
    url =  models.URLField('链接', max_length=200, blank=True, null=True)
    acct = models.ForeignKey(Account, verbose_name='账户',
                             on_delete=models.PROTECT)
    cat = models.ForeignKey(Category, verbose_name='类别',
                            on_delete=models.PROTECT)
    risk = models.ForeignKey(Risk, verbose_name='风险级别',
                             on_delete=models.PROTECT)
    isopen = models.BooleanField('是否存续')
    start = models.DateField('开始日期', blank=True, null=True)
    end = models.DateField('结束日期', blank=True, null=True)
    quote_id = models.CharField('查询代号', max_length=500, blank=True, null=True)
    current_price = models.DecimalField('现价', max_digits=16, decimal_places=4,
                                        blank=True, null=True)
    buy_amount = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    sell_amount = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    amount = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    buy_value = models.DecimalField(max_digits=16, decimal_places=2, null=True)
    sell_value = models.DecimalField(max_digits=16, decimal_places=2, null=True)
    value = models.DecimalField('现存价值', max_digits=16, decimal_places=2,
                                null=True)
    dividends = models.DecimalField('分红', max_digits=16, decimal_places=2,
                                    null=True)
    irr = models.DecimalField('年化率', max_digits=16, decimal_places=4, null=True)
    local_irr = models.DecimalField('本币年化率', max_digits=16, decimal_places=4, null=True)
    comment = models.CharField('注释', max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    def currency(self):
        return self.acct.currency
    currency.short_description = '币种'

    def bank(self):
        return format_html(
            '<a href="/admin/inv/account/?bank__id__exact={bank_id}">{bank}</a>',
            bank_id=self.acct.bank.id, bank=self.acct.bank)
    bank.short_description = '银行'

    def net_value(self):
        value = -self.value
        if self.isopen and self.current_price:
            value += self.amount*self.current_price
        return format_html(
            '<a href="{link}">{value}</a>',
            link=reverse('inv:proj_stat', kwargs={'projid': self.id}),
            value='{0:0.2f}'.format(value))
    net_value.short_description = '净值'

    def buy_price(self):
        if self.buy_amount:
            return self.buy_value/self.buy_amount
    buy_price.short_description = '买入均价'

    def sell_price(self):
        if self.sell_amount:
            return self.sell_value/self.sell_amount
    sell_price.short_description = '卖出均价'

    def avg_price(self):
        if self.amount:
            return '{0:0.4f}'.format(self.value/self.amount)
    avg_price.short_description = '成本均价'

    def buy_sell_rate(self):
        income = self.sell_value+self.dividends+self.amount*self.current_price
        return 100*income/self.buy_value - 100

    def net_value_rate(self):
        if self.isopen and self.current_price and self.value:
            return 100*(self.amount*self.current_price)/self.value - 100

    def update_from_rec(self):
        self.buy_amount, self.sell_amount = 0, 0
        self.buy_value, self.sell_value = 0, 0
        self.dividends = 0
        for r in self.invrec_set.all():
            if r.cat == 1:
                self.buy_amount += r.amount
                self.buy_value += r.value
            elif r.cat == 2:
                self.sell_amount += r.amount
                self.sell_value += r.value
            elif r.cat == 3:
                self.dividends += r.value
        self.amount = self.buy_amount - self.sell_amount
        self.value = self.buy_value - self.sell_value - self.dividends

        if self.invrec_set.count():
            self.start = min((r.date for r in self.invrec_set.all()))
            if not self.isopen:
                self.end = max((r.date for r in self.invrec_set.all()))
            self.irr = self.calc_irr(False)
            self.local_irr = self.calc_irr(True)

        self.save()

    def duration(self):
        if not self.start:
            return 0
        return ((self.end or datetime.date.today())-self.start).days
    duration.short_description = '存续天数'

    def calc_iotab(self, td, local):
        for r in self.invrec_set.all():
            value = float(r.value if r.cat == 1 else -r.value)
            if local and r.rate:
                value *= float(r.rate)
            yield (td - r.date).days, value
        if self.isopen and self.current_price:
            value = float(self.amount*self.current_price)
            if local:
                value *= float(self.acct.currency.rate)
            yield 0, -value

    def calc_irr(self, local):
        if self.isopen and self.current_price:
            td = datetime.date.today()
        else:
            td = max((r.date for r in self.invrec_set.all()))

        iotab = list(self.calc_iotab(td, local))
        def f(r):
            return sum((value*r**dur for dur, value in iotab))

        r = fsolve(f, 1.01)[0]
        return 365*100*(r-1)

    def update_current_price(self):
        if not self.quote_id or not self.cat.driver:
            return
        from . import drivers
        try:
            func = getattr(drivers, self.cat.driver)
        except AttributeError:
            return
        price = func(self.quote_id)
        if price:
            self.current_price = decimal.Decimal(price)
            self.update_from_rec()
            self.save()


class InvRec(models.Model):

    class Meta:
        verbose_name = '投资记录'
        verbose_name_plural = '投资记录'

    CAT_CHOICES = (
        (1, '买'),
        (2, '卖'),
        (3, '分红'),
    )

    proj = models.ForeignKey(InvProj, verbose_name='投资项目',
                             on_delete=models.PROTECT)
    date = models.DateField('日期')
    cat = models.IntegerField('类别', choices=CAT_CHOICES)
    amount = models.DecimalField('数额', max_digits=16, decimal_places=4)
    price = models.DecimalField('价格', max_digits=16, decimal_places=4, blank=True)
    value = models.DecimalField('总价', max_digits=16, decimal_places=2, blank=True)
    commission = models.DecimalField('佣金', max_digits=16, decimal_places=2,
                                     blank=True)
    rate = models.DecimalField('汇率', max_digits=12, decimal_places=2,
                               blank=True, null=True)

    def __str__(self):
        return f'{self.proj.name}({self.date})'

    def auto_complete(self):
        if self.cat == 3:
            return
        if self.amount is not None and self.price is not None\
           and self.value is not None and self.commission is None:
            self.commission = self.value - self.amount*self.price
        elif self.amount is not None and self.price is not None\
             and self.value is None and self.commission is not None:
            self.value = self.commission + self.amount*self.price
        elif self.amount is not None and self.price is None\
             and self.value is not None and self.commission is not None:
            self.price = (self.value-self.commission) / self.amount

    # 如果同时创建一个proj的多个rec，会导致update_from_rec被执行多次。
    # 暂时不管了。未来可能通过flag解决。
    def save(self, *args, **kwargs):
        self.auto_complete()
        if not self.pk:
            self.proj.acct.value -= (self.value if self.cat == 1 else -self.value)
        r = super().save(*args, **kwargs)
        self.proj.update_from_rec()
        return r

    def delete(self, *args, **kwargs):
        r = super().delete(*args, **kwargs)
        self.proj.update_from_rec()
        return r
