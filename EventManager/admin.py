from django.contrib import admin
from .models import Event, Consumer

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    readonly_fields = ('data', 'metadata', 'created_at')

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_event', 'updated_at')
