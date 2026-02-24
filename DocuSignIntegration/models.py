from django.db import models
from Questionnaire.models import Questionnaire


class DocuSignFieldMapping(models.Model):

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name='docusign_mappings',
        null=True, blank=True
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
        return self.name
