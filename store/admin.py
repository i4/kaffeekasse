# SPDX-License-Identifier: GPL-3.0-or-later

import django.contrib.auth.admin
import django.contrib.auth.models
from django.contrib import admin

import store.models as models


class AppendOnlyModelAdmin(admin.ModelAdmin):
    """
    Disallow changing or deleting the model. Adding new instances is
    permitted.
    """

    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

class ReadOnlyModelAdmin(AppendOnlyModelAdmin):
    """
    Disallow changing, deleting or adding objects of this model.
    """

    def has_add_permission(self, request):
        return False


class UserDataInline(admin.StackedInline):
    model = models.UserData
    can_delete = False
    verbose_name_plural = 'Data'

class UserAdmin(django.contrib.auth.admin.UserAdmin):
    list_display = ('username', 'money', 'first_name', 'last_name', 'email', 'is_staff')
    def money(self, obj):
        return obj.userdata.money

    inlines = (UserDataInline,)

    class Media:
        js = ('admin/js/misc.js',)

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
class ChargeAdmin(AppendOnlyModelAdmin):
    list_display = ('time_stamp', 'user', 'amount', 'annulled')
    # "annulled" to prevent enabling it when adding new objects
    readonly_fields = ('time_stamp', 'annulled')

    def save_model(self, request, obj, form, change):
        assert not change
        assert not obj.annulled
        # TODO: this is hacky and duplicates code from backend.py
        # Update user's money value
        obj.user.money += obj.amount
        obj.user.save()
        super().save_model(request, obj, form, change)


@admin.register(models.Purchase)
class PurchaseAdmin(ReadOnlyModelAdmin):
    list_display = ('time_stamp', 'user', 'product', 'price', 'annulled')
    readonly_fields = ('time_stamp',)


@admin.register(models.Transfer)
class TransferAdmin(AppendOnlyModelAdmin):
    list_display = ('time_stamp', 'sender', 'receiver', 'amount', 'annulled')
    # "annulled" to prevent enabling it when adding new objects
    readonly_fields = ('time_stamp', 'annulled')

    def save_model(self, request, obj, form, change):
        assert not change
        assert not obj.annulled
        # TODO: this is hacky and duplicates code from backend.py
        # Update users' money value
        obj.sender.money -= obj.amount
        obj.sender.save()
        obj.receiver.money += obj.amount
        obj.receiver.save()
        super().save_model(request, obj, form, change)


@admin.register(models.Login)
class LoginAdmin(ReadOnlyModelAdmin):
    list_display = ('user', 'time_stamp')
    readonly_fields = ('time_stamp',)
