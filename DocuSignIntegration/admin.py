from django.contrib import admin
from .models import DocuSignFieldMapping


@admin.register(DocuSignFieldMapping)
class DocuSignFieldMappingAdmin(admin.ModelAdmin):
    list_display = ('name', 'submission_form')
