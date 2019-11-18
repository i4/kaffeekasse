import django.contrib.auth.admin
import django.contrib.auth.models
import django.forms.models
from django.contrib import admin

import store.models as models


class AlwaysChangedModelForm(django.forms.models.ModelForm):
    def has_changed(self):
        return True

class UserDataInline(admin.StackedInline):
    model = models.UserData
    can_delete = False
    verbose_name_plural = 'Data'
    # When creating a new user with default values Django won't write a
    # UserData to the database. Force creating a new object by telling Django
    # the value has changed. Thanks to Daniel for the idea
    # https://stackoverflow.com/questions/3657709/how-to-force-save-an-empty-unchanged-django-admin-inline/3734700#3734700
    form = AlwaysChangedModelForm

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
