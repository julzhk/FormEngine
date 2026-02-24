from django.db import models


class Questionnaire(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class QuestionnaireSubmission(models.Model):
    questionnaire = models.ForeignKey(
        'Questionnaire', on_delete=models.CASCADE, related_name='submissions'
    )
    responses = models.JSONField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.questionnaire.name} — {self.submitted_at:%Y-%m-%d %H:%M}"


class Page(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name='pages'
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    content = models.TextField(
        help_text=(
            'Jinja2 template content. Use custom tags and context variables '
            'to compose question blocks and other components.'
        )
    )

    class Meta:
        ordering = ['order']
        unique_together = ('questionnaire', 'order')

    def __str__(self):
        return f"{self.questionnaire.name} — {self.title}"
