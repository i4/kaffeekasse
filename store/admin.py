from django.contrib import admin

import store.models as models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'is_active', 'is_staff', 'money')
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'pk_login_enabled', 'money')
        }),
    )
    pass

@admin.register(models.UserIdentifier)
class UserIdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'identifier_type', 'user')
    fields = ('identifier', 'identifier_type', 'user')

@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'stock')
    fields = ('name', 'price', 'category', 'stock')

@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'toplevel', 'sublevel')
    fields = ('toplevel', 'sublevel')

@admin.register(models.ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'identifier_type', 'product')
    fields = ('identifier', 'identifier_type', 'product')
