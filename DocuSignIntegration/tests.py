import json
from django.test import TestCase
from FormComposer.models import SubmissionForm
from .models import DocuSignFieldMapping

class DocuSignFieldMappingTest(TestCase):
    def setUp(self):
        self.form = SubmissionForm.objects.create(name="Test Form")

    def test_render_json_template(self):
        mapping = DocuSignFieldMapping.objects.create(
            submission_form=self.form,
            name="Test Mapping",
            template_string={
                "envelope": {
                    "emailSubject": "Please sign: {{ q1 }}",
                    "templateId": "abc-123",
                    "templateRoles": [
                        {
                            "email": "{{ q2 }}",
                            "name": "Signer 1",
                            "roleName": "Signer"
                        }
                    ]
                }
            }
        )
        
        data_dict = {
            "q1": "Contract A",
            "q2": "test@example.com"
        }
        
        rendered_json = mapping.render(data_dict)
        rendered_data = json.loads(rendered_json)
        
        self.assertEqual(rendered_data["envelope"]["emailSubject"], "Please sign: Contract A")
        self.assertEqual(rendered_data["envelope"]["templateRoles"][0]["email"], "test@example.com")
        self.assertEqual(rendered_data["envelope"]["templateId"], "abc-123")

    def test_render_json_template_with_quotes(self):
        mapping = DocuSignFieldMapping.objects.create(
            submission_form=self.form,
            name="Test Mapping Quotes",
            template_string={
                "message": "He said: {{ q1 }}"
            }
        )
        
        data_dict = {
            "q1": '"Hello World"'
        }
        
        rendered_json = mapping.render(data_dict)
        rendered_data = json.loads(rendered_json)
        
        self.assertEqual(rendered_data["message"], 'He said: "Hello World"')
