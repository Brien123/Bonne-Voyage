from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, BusOperator, BusOperatorImage

class UserAdmin(BaseUserAdmin):
    # Fields to be displayed in the admin list view
    list_display = ('phone_number', 'first_name', 'last_name', 'created_at', 'is_superuser')
    
    # Fields to be used for searching in the admin interface
    search_fields = ('first_name', 'last_name', 'phone_number')
    
    # Filters to be used in the admin interface
    list_filter = ('created_at', 'is_superuser')
    
    # Fieldsets for organizing the form in the admin interface
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    # Fields to be displayed when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    # Specify which field to use for ordering the list view
    ordering = ('phone_number',)
    
class BusOperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'email', 'created_at')
    search_fields = ('name', 'email', 'contact')
    list_filter = ('created_at',)

admin.site.register(User, UserAdmin)
admin.site.register(BusOperator, BusOperatorAdmin)
admin.site.register(BusOperatorImage)