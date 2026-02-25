from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from EventManager.models import Event

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

# class PetProcessor(Processor):
#     @dataclasses.dataclass
#     class Data_v4:
#         q1: str|None = None
#         q2: str|None = None
#         q3: str|None = None
# 
#     def do_process(self,data_dict:dict, avro_schema_registry:SchemaRegistry):
#         if avro_schema_registry.version !=  4:
#             print("Schema version mismatch, skipping processing")
#             return
#         try:
#             data:'Data_v4' = self.__class__.Data_v4(**data_dict)
#             print(f"PetProcessor processing data: {data}")
#         except TypeError as e:
#             print(f"Error parsing data: {e}: data schema mismatch")
#             return
#             
#         # Write out a text file with filename being the current datetime
#         filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".txt"
#         content = str(data.q1) + "\n" + str(data.q2) + "\n" + str(data.q3)
#         
#         with open(filename, "w") as f:
#             f.write(content)
#         print(f"Wrote data to {filename}")

