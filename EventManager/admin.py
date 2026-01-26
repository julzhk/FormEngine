from django.contrib import admin
from .models import Event, ConsumerOffset

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    readonly_fields = ('data', 'metadata', 'created_at')

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ConsumerOffset)
class ConsumerOffsetAdmin(admin.ModelAdmin):
    list_display = ('processor_class', 'offset', 'updated_at')
