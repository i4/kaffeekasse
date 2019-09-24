from django.contrib import admin
from .models import User, Product


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'is_active', 'is_staff', 'money')
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name')
        }),
    )
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    fields = ('name', 'price', 'category')