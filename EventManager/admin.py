from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from .models import ConsumerOffset, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    readonly_fields = ('data', 'metadata', 'created_at')
    change_list_template = 'admin/eventmanager/event/change_list.html'

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                'process-events/',
                self.admin_site.admin_view(self.process_events_view),
                name='eventmanager_event_process_events',
            ),
        ]
        return custom_urls + super().get_urls()

    def process_events_view(self, request):
        from DocuSignIntegration.processor import DocuSignProcessor
        try:
            result = DocuSignProcessor.consume()
            self.message_user(request, f"Process events completed: {result}", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error processing events: {e}", messages.ERROR)
        return HttpResponseRedirect(reverse('admin:EventManager_consumeroffset_changelist'))


@admin.register(ConsumerOffset)
class ConsumerOffsetAdmin(admin.ModelAdmin):
    list_display = ('processor_class', 'offset', 'updated_at')
    change_list_template = 'admin/eventmanager/consumeroffset/change_list.html'
