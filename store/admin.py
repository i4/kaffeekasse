from django.contrib import admin
from .models import User, Product, ProductCategory, UserIdentifier, ProductIdentifier


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'is_active', 'is_staff', 'money')
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'pk_login_enabled', 'money')
        }),
    )
    pass

@admin.register(UserIdentifier)
class UserIdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'identifier_type', 'user')
    fields = ('identifier', 'identifier_type', 'user')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'stock')
    fields = ('name', 'price', 'category', 'stock')

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'toplevel', 'sublevel')
    fields = ('toplevel', 'sublevel')

@admin.register(ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'identifier_type', 'product')
    fields = ('identifier', 'identifier_type', 'product')
