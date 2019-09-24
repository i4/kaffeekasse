from django.contrib import admin
from .models import User


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
