from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect

from .models import Currency, Category, Bank, Account, AccountCategory, AccountRec, Risk, InvProj, InvRec


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'accounts', 'investments', 'total', 'total_in_local')
    actions = ['update_current_price',]

    def accounts(self, currency):
        return sum(((-a.value if a.cat.cat in {2, 4} else a.value)
                    for a in currency.account_set.all()))
    accounts.short_description = '账户余额'

    def investments(self, currency):
        return sum((p.value for p in InvProj.objects.filter(acct__currency=currency, isopen=True).all()))
    investments.short_description = '投资余额'

    def total(self, currency):
        return self.accounts(currency) + self.investments(currency)
    total.short_description = '总计余额'

    def total_in_local(self, currency):
        return '{0:0.2f}'.format(self.total(currency)*currency.rate)
    total_in_local.short_description = '以本币计总余额'

    def update_current_price(self, request, queryset):
        for c in queryset:
            c.update_current_price()
    update_current_price.short_description = '更新汇率'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'cat', 'value', 'value_in_local')

    def value(self, cat):
        s = sum((a.value for a in cat.account_set.all()))
        s += sum((p.value for p in cat.invproj_set.filter(isopen=True).all()))
        return s
    value.short_description = '总计余额'

    def value_in_local(self, cat):
        s = sum((a.value*a.currency.rate for a in cat.account_set.all()))
        s += sum((p.value*p.acct.currency.rate
                  for p in cat.invproj_set.filter(isopen=True).all()))
        return '{0:0.2f}'.format(s)
    value_in_local.short_description = '以本币计总余额'


class AccountInline(admin.TabularInline):
    model = Account


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')
    inlines = [AccountInline,]

    def value(self, bank):
        s = sum(((-a.value if a.cat.cat in {2, 4} else a.value)*a.currency.rate
                 for a in bank.account_set.all()))
        s += sum((p.value*p.acct.currency.rate
                  for p in InvProj.objects.filter(acct__bank=bank, isopen=True).all()))
        return s
    value.short_description = '总计余额'


# class AccountRecInline(admin.TabularInline):
#     model = AccountRec


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('bank', 'name', 'currency', 'cat', 'value')
    list_display_links = ('name',)
    list_editable = ('value',)
    list_filter = ['bank', 'currency', 'cat']
    search_fields = ['name',]
    # inlines = [AccountRecInline,]


@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'cat')


@admin.register(AccountRec)
class AccountRecAdmin(admin.ModelAdmin):
    list_display = ('acct', 'date', 'cat', 'value', 'comment')
    list_display_links = ('date',)
    list_editable = ('value', 'comment')
    list_filter = ['acct', 'date', 'cat']


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'percentage')

    def value(self, risk):
        return sum((p.value*p.acct.currency.rate
                    for p in risk.invproj_set.filter(isopen=True).all()))
    value.short_description = '总计余额'

    def percentage(self, risk):
        total = sum((p.value*p.acct.currency.rate
                     for p in InvProj.objects.filter(isopen=True).all()))
        return '{0:0.2f}'.format(100*self.value(risk)/total)
    percentage.short_description = '百分比'


class InvRecInline(admin.TabularInline):
    model = InvRec


@admin.register(InvProj)
class InvProjAdmin(admin.ModelAdmin):
    list_display = ('name', 'isopen', 'currency', 'bank', 'cat', 'risk',
                    'start', 'end', 'duration',
                    'value', 'avg_price', 'current_price', 'net_value')
    # list_display_links = ('start',)
    date_hierarchy = 'end'
    list_filter = ['isopen', 'acct__currency', 'acct__bank', 'cat', 'risk']
    exclude = ('start', 'amount', 'buy_amount', 'sell_amount',
               'value', 'buy_value', 'sell_value', 'dividends', 'irr', 'local_irr')
    inlines = [InvRecInline,]
    actions = ['update_current_price', 'update_from_rec']

    def view_on_site(self, obj):
        return reverse('inv:proj_stat', kwargs={'projid': obj.id})

    def save_model(self, request, obj, form, change):
        obj.update_from_rec()
        super().save_model(request, obj, form, change)

    def update_current_price(self, request, queryset):
        for p in queryset:
            p.update_current_price()
    update_current_price.short_description = '更新现价'

    def update_from_rec(self, request, queryset):
        for p in queryset:
            p.update_from_rec()
    update_from_rec.short_description = '更新统计'


@admin.register(InvRec)
class InvRecAdmin(admin.ModelAdmin):
    list_display = ('proj', 'date', 'cat', 'amount', 'price', 'value', 'rate', 'commission')
