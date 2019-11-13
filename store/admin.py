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
    list_display = ('user', 'identifier_type', 'identifier')


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock')


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('toplevel', 'sublevel')
    list_display_links = ('sublevel',)


@admin.register(models.ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ('product', 'identifier_type', 'identifier')
