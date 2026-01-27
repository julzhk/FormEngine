import dataclasses
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from AvroSchemaManager.models import SchemaRegistry

logger = logging.getLogger(__name__)


class Processor(ABC):
    @classmethod
    def consume(cls):
        from EventManager.models import Event, ConsumerOffset
        from FormComposer.models import SubmissionForm

        processor_class_path = f"{cls.__module__}.{cls.__name__}"
        
        # Get or create the offset for this processor
        offset_record, created = ConsumerOffset.objects.get_or_create(
            processor_class=processor_class_path
        )
        
        # Determine the starting point
        last_event_id = offset_record.offset_id if offset_record.offset else 0
        
        # Fetch all new events for this processor
        # We filter by processor_class in metadata to ensure this processor only handles its own events
        new_events = Event.objects.filter(
            id__gt=last_event_id,
            metadata__processor_class=processor_class_path
        ).order_by('id')
        
        last_processed_event = None
        processor_instance = cls()
        for event in new_events:
            try:
                form_id = event.metadata.get('form_id')
                form = SubmissionForm.objects.get(pk=form_id)
                processor_instance.process(event.data, form)
                last_processed_event = event
            except Exception as e:
                print(f"Error processing event {event.id}: {e}")
                # Depending on requirements, we might want to stop or continue
                # For now, let's stop updating the offset if a critical failure occurs 
                # or just log and continue if it's a specific event issue.
                # If we want to guarantee processing, we should probably break here.
                break
        
        # Update the offset if we processed any events
        if last_processed_event:
            offset_record.offset = last_processed_event
            offset_record.save()

    def process(self, data, form):
        # data is avro serialized bytes
        deserialized_dict, avro_schema_registry = form.avro_deserialize(data)
        print(f" logging data: {deserialized_dict}")
        logger.info(f" processing data: {deserialized_dict}")
        self.do_process(deserialized_dict,avro_schema_registry)

    @abstractmethod
    def do_process(self, data_dict:dict, avro_schema_registry:SchemaRegistry):
        pass

class PetProcessor(Processor):
    @dataclasses.dataclass
    class Data_v4:
        q1: str|None = None
        q2: str|None = None
        q3: str|None = None

    def do_process(self,data_dict:dict, avro_schema_registry:SchemaRegistry):
        if avro_schema_registry.version !=  4:
            print("Schema version mismatch, skipping processing")
            return
        try:
            data:'Data_v4' = self.__class__.Data_v4(**data_dict)
            print(f"PetProcessor processing data: {data}")
        except TypeError as e:
            print(f"Error parsing data: {e}: data schema mismatch")
            return
            
        # Write out a text file with filename being the current datetime
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".txt"
        content = str(data.q1) + "\n" + str(data.q2) + "\n" + str(data.q3)
        
        with open(filename, "w") as f:
            f.write(content)
        print(f"Wrote data to {filename}")

