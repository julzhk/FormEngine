import json
import logging
from datetime import datetime

from FormComposer.processor import Processor

logger = logging.getLogger(__name__)


class DocuSignProcessor(Processor):
    @classmethod
    def event_filter(cls) -> dict:
        return {'metadata__source': 'questionnaire'}

    def do_process(self, data_dict: dict, metadata: dict):
        from DocuSignIntegration.models import DocuSignFieldMapping

        questionnaire_id = metadata.get('questionnaire_id')
        mapping = DocuSignFieldMapping.objects.filter(questionnaire_id=questionnaire_id).first()
        if not mapping:
            logger.warning(f"No DocuSign mapping found for questionnaire {questionnaire_id}")
            return f"No mapping for questionnaire {questionnaire_id}"

        rendered_json = mapping.render(data_dict)

        try:
            payload = json.loads(rendered_json)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from template rendering: {e}\nRendered output: {rendered_json}")
            return f"JSON decode error: {e}"

        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".txt"
        with open(filename, "w") as f:
            f.write(rendered_json)

        logger.info(f"DocuSign payload written to {filename}: {json.dumps(payload, indent=2)}")
        return f"Wrote DocuSign payload to {filename}"
