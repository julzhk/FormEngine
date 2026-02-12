from django.db import models
from FormComposer.models import SubmissionForm


class DocuSignFieldMapping(models.Model):
    submission_form = models.ForeignKey(
        SubmissionForm, on_delete=models.CASCADE,
        related_name='docusign_mappings'
    )
    name = models.CharField(max_length=255)
    template_string = models.JSONField(
        help_text="JSON object where values can be Django Templates. "
                  "Form field values are available as template variables (e.g. {{ q1 }}, {{ q2 }})."
    )

    def render(self, data_dict: dict) -> str:
        """Render the JSON template with form data as context, returning a JSON string."""
        import json
        from django.template import Template, Context

        def render_value(value):
            return Template("{% autoescape off %}" + json.dumps(value) + "{% endautoescape %}").render(Context(data_dict))

        rendered_data = render_value(self.template_string)
        return rendered_data

    def __str__(self):
        return f"{self.name} ({self.submission_form})"
