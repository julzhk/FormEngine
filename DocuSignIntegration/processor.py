from datetime import datetime
import json
import logging
from FormComposer.processor import Processor
from AvroSchemaManager.models import SchemaRegistry

logger = logging.getLogger(__name__)


class DocuSignProcessor(Processor):
    def do_process(self, data_dict: dict, avro_schema_registry: SchemaRegistry):
        from DocuSignIntegration.models import DocuSignFieldMapping
        from FormComposer.models import SubmissionForm

        schema_name = avro_schema_registry.name
        form_id = int(schema_name.split('_')[0].replace('Form', ''))
        form = SubmissionForm.objects.get(pk=form_id)

        mapping = DocuSignFieldMapping.objects.filter(submission_form=form).first()
        if not mapping:
            logger.warning(f"No DocuSign mapping found for form {form.id} ({form.name})")
            return

        rendered_json = mapping.render(data_dict)

        try:
            payload = json.loads(rendered_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from template rendering: {e}")
            logger.error(f"Rendered output: {rendered_json}")
            return

        logger.info(f"DocuSign payload for form {form.name}: {json.dumps(payload, indent=2)}")
        # Write out a text file with filename being the current datetime
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".txt"
        with open(filename, "w") as f:
            f.write(rendered_json)
        print(f"Wrote data to {filename}")

        print(f"DocuSign payload: {json.dumps(payload, indent=2)}")
