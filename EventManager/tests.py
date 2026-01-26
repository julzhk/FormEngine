from django.test import TestCase
from .models import Event, Consumer

class EventModelTest(TestCase):
    def test_event_creation(self):
        event = Event.objects.create(
            data=b"test data",
            metadata={"source": "test"}
        )
        self.assertEqual(event.data, b"test data")
        self.assertEqual(event.metadata, {"source": "test"})
        self.assertIsNotNone(event.created_at)

    def test_event_immutability(self):
        event = Event.objects.create(
            data=b"initial",
            metadata={}
        )
        with self.assertRaises(TypeError):
            event.data = b"updated"
            event.save()

class ConsumerModelTest(TestCase):
    def test_consumer_creation_and_tracking(self):
        event1 = Event.objects.create(data=b"event 1", metadata={})
        event2 = Event.objects.create(data=b"event 2", metadata={})
        
        consumer = Consumer.objects.create(name="TestConsumer")
        self.assertNil(consumer.last_event)
        
        consumer.last_event = event1
        consumer.save()
        self.assertEqual(consumer.last_event, event1)
        
        consumer.last_event = event2
        consumer.save()
        self.assertEqual(consumer.last_event, event2)

    def assertNil(self, value):
        self.assertIsNone(value)
