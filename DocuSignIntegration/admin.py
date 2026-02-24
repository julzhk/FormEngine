from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from .models import DocuSignFieldMapping


@admin.register(DocuSignFieldMapping)
class DocuSignFieldMappingAdmin(admin.ModelAdmin):
    list_display = ('name', )
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
