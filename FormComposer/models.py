from django.db import models

def get_processor_choices():
    from .processor import Processor
    # Get all subclasses of Processor
    subclasses = Processor.__subclasses__()
    return [(f"{sub.__module__}.{sub.__name__}", sub.__name__) for sub in subclasses]

class Question(models.Model):
    label = models.CharField(max_length=255)
    # Currently only text fields are supported
    field_type = models.CharField(max_length=50, default='text')

    def __str__(self):
        return self.label

class FormPage(models.Model):
    title = models.CharField(max_length=255)
    questions = models.ManyToManyField(Question, through='FormPageQuestion')

    def __str__(self):
        return self.title

class SubmissionForm(models.Model):
    name = models.CharField(max_length=255)
    pages = models.ManyToManyField(FormPage, through='SubmissionFormPage')
    processor_class = models.CharField(
        max_length=255, 
        choices=get_processor_choices,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

class FormPageQuestion(models.Model):
    form_page = models.ForeignKey(FormPage, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('form_page', 'order')

class SubmissionFormPage(models.Model):
    submission_form = models.ForeignKey(SubmissionForm, on_delete=models.CASCADE)
    form_page = models.ForeignKey(FormPage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('submission_form', 'order')
