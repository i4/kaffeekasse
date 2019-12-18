# SPDX-License-Identifier: GPL-3.0-or-later

import django.contrib.auth.admin
import django.contrib.auth.models
import django.urls
from django.contrib import admin
from django.db import transaction
from django.utils.translation import gettext_lazy as _

import store.models as models


def is_delete_for_different_object(admin, request):
    """
    Django manages (delete) permissions for the admin interface globally. We
    want to disallow deleting an object (e.g. UserData) but permit deleting it
    when part of a larger operation (e.g. when deleting a User).
    """

    if request.method != 'POST':
        return False
    if 'action' not in request.POST:
        return False
    if request.POST['action'] != 'delete_selected':
        return False

    # Permit the operation if the request tries to delete a different object
    admin_url = django.urls.reverse('admin:{0}_{1}_changelist'.format(
        admin.model._meta.app_label, admin.model._meta.model_name))
    if request.path.startswith(admin_url):
        return False

    return True


class AppendOnlyModelAdmin(admin.ModelAdmin):
    """
    Disallow changing or deleting the model. Adding new instances is
    permitted.
    """

    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        if is_delete_for_different_object(self, request):
            return True
        return False

class ReadOnlyModelAdmin(AppendOnlyModelAdmin):
    """
    Disallow changing, deleting or adding objects of this model.
    """

    def has_add_permission(self, request):
        return False


@admin.register(models.UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('username', 'idm', 'money', 'shown_on_login_screen')
    def username(self, obj):
        return obj.auth.username
    username.admin_order_field = 'auth__username'

    # UserData without a User is useless, prevent it
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        if is_delete_for_different_object(self, request):
            return True
        return False

    readonly_fields = ('auth', 'money', 'last_mail')

    # For autocomplete_fields
    ordering = ('auth__username',)
    search_fields = ('auth__username', 'auth__first_name', 'auth__last_name',
                     'idm')

class UserDataInline(admin.StackedInline):
    model = models.UserData
    can_delete = False
    verbose_name_plural = 'Data'

    readonly_fields = ('money',)

class UserAdmin(django.contrib.auth.admin.UserAdmin):
    list_display = ('username', 'idm', 'money', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser')
    def idm(self, obj):
        return obj.userdata.idm
    idm.admin_order_field = 'userdata__idm'
    def money(self, obj):
        return obj.userdata.money
    money.admin_order_field = 'userdata__money'

    # Hide unimportant fields; copied from django.contrib.auth.admin.UserAdmin
    # and modified
    fieldsets = (
        (None, {'fields': ('username', 'password', 'last_login', 'is_staff', 'is_superuser')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    )

    search_fields = ('username', 'first_name', 'last_name', 'email',
                     'userdata__idm')

    readonly_fields = ('last_login',)

    inlines = (UserDataInline,)

    class Media:
        js = ('admin/js/misc.js',)

admin.site.unregister(django.contrib.auth.models.User)
admin.site.register(django.contrib.auth.models.User, UserAdmin)


@admin.register(models.UserIdentifier)
class UserIdentifierAdmin(admin.ModelAdmin):
    list_display = ('user', 'ident_type', 'ident')

    search_fields = ('user__auth__username', 'user__auth__first_name',
                     'user__auth__last_name', 'user__auth__email',
                     'user__idm',
                     'ident')

    autocomplete_fields = ('user',)


@admin.register(models.UnknownUserIdentifier)
class UnknownUserIdentifierAdmin(admin.ModelAdmin):
    list_display = ('time_stamp', 'ident_type', 'ident')


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock')

    search_fields = ('name',)


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('toplevel', 'sublevel')
    list_display_links = ('sublevel',)


@admin.register(models.ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ('product', 'ident_type', 'ident')

    search_fields = ('product__name', 'ident')

    autocomplete_fields = ('product',)


@admin.register(models.Charge)
class ChargeAdmin(AppendOnlyModelAdmin):
    list_display = ('time_stamp', 'user', 'amount', 'admin', 'comment', 'annulled')
    # "annulled" to prevent enabling it when adding new objects
    readonly_fields = ('time_stamp', 'admin', 'annulled')

    search_fields = ('user__auth__username', 'user__auth__first_name',
                     'user__auth__last_name', 'user__auth__email',
                     'user__idm',
                     'comment')

    autocomplete_fields = ('user',)

    def save_model(self, request, obj, form, change):
        assert not change
        assert not obj.annulled
        # TODO: this is hacky and duplicates code from backend.py
        # Update user's money value
        with transaction.atomic():
            user = models.UserData.objects.get(id=obj.user.id)
            user.money += obj.amount
            user.save()
        obj.admin = request.user.userdata
        super().save_model(request, obj, form, change)


@admin.register(models.Purchase)
class PurchaseAdmin(ReadOnlyModelAdmin):
    list_display = ('time_stamp', 'user', 'product', 'price', 'annulled')
    readonly_fields = ('time_stamp',)

    search_fields = ('user__auth__username', 'user__auth__first_name',
                     'user__auth__last_name', 'user__auth__email',
                     'user__idm',
                     'product__name')


@admin.register(models.Transfer)
class TransferAdmin(AppendOnlyModelAdmin):
    list_display = ('time_stamp', 'sender', 'receiver', 'amount', 'admin', 'comment', 'annulled')
    # "annulled" to prevent enabling it when adding new objects
    readonly_fields = ('time_stamp', 'admin', 'annulled')

    search_fields = ('sender__auth__username', 'sender__auth__first_name',
                     'sender__auth__last_name', 'sender__auth__email',
                     'sender__idm',
                     'receiver__auth__username', 'receiver__auth__first_name',
                     'receiver__auth__last_name', 'receiver__auth__email',
                     'receiver__idm',
                     'comment')

    autocomplete_fields = ('sender', 'receiver')

    def save_model(self, request, obj, form, change):
        assert not change
        assert not obj.annulled
        # TODO: this is hacky and duplicates code from backend.py
        # Update users' money value
        with transaction.atomic():
            sender = models.UserData.objects.get(id=obj.sender.id)
            sender.money -= obj.amount
            sender.save()
            receiver = models.UserData.objects.get(id=obj.receiver.id)
            receiver.money += obj.amount
            receiver.save()
        obj.admin = request.user.userdata
        super().save_model(request, obj, form, change)


# We don't use groups, hide it
admin.site.unregister(django.contrib.auth.models.Group)
