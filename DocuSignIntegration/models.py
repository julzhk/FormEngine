from django.db import models
from FormComposer.models import SubmissionForm


class DocuSignFieldMapping(models.Model):
    submission_form = models.ForeignKey(
        SubmissionForm, on_delete=models.CASCADE,
        related_name='docusign_mappings'
    )
    name = models.CharField(max_length=255)
    template_string = models.TextField(
        help_text="Django Template that renders to a JSON string. "
                  "Form field values are available as template variables (e.g. {{ q1 }}, {{ q2 }})."
    )

    def render(self, data_dict: dict) -> str:
        """Render the template with form data as context, returning a JSON string."""
        from django.template import Template, Context
        template = Template(self.template_string)
        context = Context(data_dict)
        return template.render(context)

    def __str__(self):
        return f"{self.name} ({self.submission_form})"
