from django.contrib import admin
from .models import *

# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'is_read', 'created_at']
    
admin.site.register(Notifications, NotificationAdmin)
