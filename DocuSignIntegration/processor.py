from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class Processor(ABC):
    @classmethod
    def event_filter(cls) -> dict:
        """Extra filter kwargs applied when querying for new events."""
        return {}

    @classmethod
    def consume(cls):
        from EventManager.models import Event, ConsumerOffset

        processor_class_path = f"{cls.__module__}.{cls.__name__}"

        offset_record, _ = ConsumerOffset.objects.get_or_create(
            processor_class=processor_class_path
        )

        last_event_id = offset_record.offset_id if offset_record.offset else 0

        new_events = Event.objects.filter(
            id__gt=last_event_id,
            **cls.event_filter()
        ).order_by('id')

        last_processed_event = None
        r = f"No new events for {processor_class_path}."
        processor_instance = cls()
        for event in new_events:
            try:
                r = processor_instance.process(event)
                last_processed_event = event
            except Exception as e:
                r = f"Error processing event {event.id}: {e}"
                logger.error(r)
                break

        if last_processed_event:
            offset_record.offset = last_processed_event
            offset_record.save()
        return r

    def process(self, event):
        logger.info(f"Processing event {event.id}: {event.data}")
        return self.do_process(event)

    @abstractmethod
    def do_process(self, event: Event) -> str:
        raise NotImplementedError


class DocuSignProcessor(Processor):
    @classmethod
    def event_filter(cls) -> dict:
        return {'metadata__source': 'questionnaire'}

    def do_process(self, event: Event) -> str:
        from DocuSignIntegration.models import DocuSignFieldMapping
        data_dict = event.data
        metadata = event.metadata
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

def get_processor_choices():
    subclasses = get_processor_klasses()
    return [(f"{sub.__module__}.{sub.__name__}", sub.__name__) for sub in subclasses]


def get_processor_klasses() -> list[type[Processor]]:
    # Get all subclasses of Processor
    subclasses = Processor.__subclasses__()
    return subclasses
