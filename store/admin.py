from django.contrib import admin

import store.models as models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'money',
            'pk_login_enabled', 'is_active', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'pk_login_enabled', 'money')
        }),
    )


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
    list_display = ('token', 'time_stamp', 'user', 'amount',
            'annullated')
    readonly_fields = ('time_stamp',)


@admin.register(models.Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('token', 'time_stamp', 'user', 'product', 'price',
            'annullated')
    readonly_fields = ('time_stamp',)


@admin.register(models.Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('token', 'time_stamp', 'sender', 'receiver', 'amount',
            'annullated')
    readonly_fields = ('time_stamp',)


@admin.register(models.Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ('user', 'time_stamp')
    readonly_fields = ('time_stamp',)


admin.site.register(models.Token)
