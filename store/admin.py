import django.contrib.auth.admin
import django.contrib.auth.models
from django.contrib import admin

import store.models as models


class UserDataInline(admin.StackedInline):
    model = models.UserData
    can_delete = False
    verbose_name_plural = 'Data'

class UserAdmin(django.contrib.auth.admin.UserAdmin):
    inlines = (UserDataInline,)

admin.site.unregister(django.contrib.auth.models.User)
admin.site.register(django.contrib.auth.models.User, UserAdmin)


@admin.register(models.UserIdentifier)
class UserIdentifierAdmin(admin.ModelAdmin):
    list_display = ('user', 'ident_type', 'ident')


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock')


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('toplevel', 'sublevel')
    list_display_links = ('sublevel',)


@admin.register(models.ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ('product', 'ident_type', 'ident')


@admin.register(models.Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ('time_stamp', 'user', 'amount',
            'annulled')
    readonly_fields = ('time_stamp',)


@admin.register(models.Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('time_stamp', 'user', 'product', 'price',
            'annulled')
    readonly_fields = ('time_stamp',)


@admin.register(models.Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('time_stamp', 'sender', 'receiver', 'amount',
            'annulled')
    readonly_fields = ('time_stamp',)


@admin.register(models.Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ('user', 'time_stamp')
    readonly_fields = ('time_stamp',)
