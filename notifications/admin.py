from django.contrib import admin
from .models import *

# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'message', 'created_at', 'is_read')
    filter_horizontal = ('recipient',) 
    
admin.site.register(Notifications, NotificationAdmin)
