from django.contrib import admin
from django.forms import Textarea

from .models import Page, Questionnaire, QuestionnaireSubmission

_MONO_ATTRS = {'style': 'font-family: monospace;'}
_MONO_FIELDS = {'content', 'completed_content'}


class PageInline(admin.StackedInline):
    model = Page
    extra = 1
    ordering = ['order']
    fields = ('title', 'order', 'content')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in _MONO_FIELDS:
            kwargs['widget'] = Textarea(attrs=_MONO_ATTRS)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    fields = ('name', 'description', 'completed_content')
    inlines = [PageInline]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in _MONO_FIELDS:
            kwargs['widget'] = Textarea(attrs=_MONO_ATTRS)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'questionnaire', 'order')
    list_filter = ('questionnaire',)
    ordering = ('questionnaire', 'order')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in _MONO_FIELDS:
            kwargs['widget'] = Textarea(attrs=_MONO_ATTRS)
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(QuestionnaireSubmission)
class QuestionnaireSubmissionAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'submitted_at')
    list_filter = ('questionnaire',)
    readonly_fields = ('questionnaire', 'responses', 'submitted_at')
