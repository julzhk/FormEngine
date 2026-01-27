from django.test import TestCase
from .models import SchemaRegistry

class SchemaRegistryModelTest(TestCase):
    def test_schema_registry_creation(self):
        schema_dict = {"type": "record", "name": "Test", "fields": []}
        schema = SchemaRegistry.objects.create(
            name="TestSchema",
            namespace="com.example",
            version=1,
            avro_schema=schema_dict
        )
        self.assertEqual(schema.name, "TestSchema")
        self.assertEqual(schema.version, 1)
        self.assertEqual(schema.avro_schema, schema_dict)
        self.assertEqual(str(schema), "TestSchema (v1)")
