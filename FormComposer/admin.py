from django.contrib import admin
from .models import Question, FormPage, FormPageQuestion, SubmissionForm, SubmissionFormPage

class FormPageQuestionInline(admin.TabularInline):
    model = FormPageQuestion
    extra = 1

class SubmissionFormPageInline(admin.TabularInline):
    model = SubmissionFormPage
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('label', 'field_type')

@admin.register(FormPage)
class FormPageAdmin(admin.ModelAdmin):
    inlines = [FormPageQuestionInline]

@admin.register(SubmissionForm)
class SubmissionFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'processor_class')
    inlines = [SubmissionFormPageInline]
    readonly_fields = ('avro_schema',)
