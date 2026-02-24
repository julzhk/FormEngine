from django.test import TestCase
from .models import Event, ConsumerOffset

class EventModelTest(TestCase):
    def test_event_creation(self):
        event = Event.objects.create(
            data={"content": "test data"},
            metadata={"source": "test"}
        )
        self.assertEqual(event.data, {"content": "test data"})
        self.assertEqual(event.metadata, {"source": "test"})
        self.assertIsNotNone(event.created_at)

    def test_event_immutability(self):
        event = Event.objects.create(
            data={"content": "initial"},
            metadata={}
        )
        with self.assertRaises(TypeError):
            event.data = {"content": "updated"}
            event.save()

class ConsumerOffsetModelTest(TestCase):
    def test_consumer_offset_creation_and_tracking(self):
        event1 = Event.objects.create(data={"content": "event 1"}, metadata={})
        event2 = Event.objects.create(data={"content": "event 2"}, metadata={})
        
        # Note: we use a string that would normally be a processor class
        processor = "FormComposer.processor.PetProcessor"
        consumer_offset = ConsumerOffset.objects.create(processor_class=processor)
        self.assertIsNone(consumer_offset.offset)
        
        consumer_offset.offset = event1
        consumer_offset.save()
        self.assertEqual(consumer_offset.offset, event1)
        
        consumer_offset.offset = event2
        consumer_offset.save()
        self.assertEqual(consumer_offset.offset, event2)
