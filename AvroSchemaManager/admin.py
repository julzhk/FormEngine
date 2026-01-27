from django.contrib import admin
from .models import SchemaRegistry

@admin.register(SchemaRegistry)
class SchemaRegistryAdmin(admin.ModelAdmin):
    list_display = ('name', 'version')
    search_fields = ('name',)
