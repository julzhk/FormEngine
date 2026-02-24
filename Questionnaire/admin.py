from django.contrib import admin

from .models import Page, Questionnaire, QuestionnaireSubmission


class PageInline(admin.StackedInline):
    model = Page
    extra = 1
    ordering = ['order']
    fields = ('title', 'order', 'content')


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    fields = ('name', 'description', 'completed_content')
    inlines = [PageInline]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'questionnaire', 'order')
    list_filter = ('questionnaire',)
    ordering = ('questionnaire', 'order')


@admin.register(QuestionnaireSubmission)
class QuestionnaireSubmissionAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'submitted_at')
    list_filter = ('questionnaire',)
    readonly_fields = ('questionnaire', 'responses', 'submitted_at')
