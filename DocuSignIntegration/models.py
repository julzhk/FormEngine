from django.db import models
from Questionnaire.models import Questionnaire


class DocuSignFieldMapping(models.Model):

    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name='docusign_mappings',
        null=True, blank=True
    )
    name = models.CharField(max_length=255)
    template_string = models.JSONField(
        help_text="JSON object where values are Jinja2 templates. "
                  "Form field values are available as variables (e.g. {{ q1 }}, {{ q2 }}). "
                  "Available filters: format_tin (e.g. {{ ssn | format_tin }})."
    )

    def render(self, data_dict: dict) -> str:
        """Render the JSON template with form data as context, returning a JSON string."""
        import json
        from DocuSignIntegration.jinja_env import environment

        template_source = json.dumps(self.template_string)
        return environment.from_string(template_source).render(**data_dict)

    def __str__(self):
        return self.name
