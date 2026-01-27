import io
import json
import fastavro
import fastavro.validation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from FormComposer.processor import Processor


def get_processor_choices():
    subclasses = get_processor_klasses()
    return [(f"{sub.__module__}.{sub.__name__}", sub.__name__) for sub in subclasses]


def get_processor_klasses() -> list[type[Processor]]:
    from .processor import Processor
    # Get all subclasses of Processor
    subclasses = Processor.__subclasses__()
    return subclasses


class Question(models.Model):
    label = models.CharField(max_length=255)
    # Currently only text fields are supported
    field_type = models.CharField(max_length=50, default='text')

    def __str__(self):
        return self.label

class FormPage(models.Model):
    title = models.CharField(max_length=255)
    questions = models.ManyToManyField(Question, through='FormPageQuestion')

    def __str__(self):
        return self.title

class SubmissionForm(models.Model):
    name = models.CharField(max_length=255)
    pages = models.ManyToManyField(FormPage, through='SubmissionFormPage')
    processor_class = models.CharField(
        max_length=255, 
        choices=get_processor_choices,
        blank=True,
        null=True
    )
    avro_schema = models.JSONField(blank=True, null=True)
    version = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        
        # We need to save first if it's new to have an ID for the schema name, 
        # but generate_avro_schema uses self.id. 
        # Actually, generate_avro_schema uses self.id in the 'name' field.
        # If it's a new object, id might be None.
        super().save(*args, **kwargs)
        # Now that we have an ID (if it was new), we can generate and save the schema
        # Note: generate_avro_schema relies on related pages/questions, 
        # which might not be there yet during the very first save if created via admin 
        # (since M2M throughs are saved after the main object).
        # However, for updates, it should work fine.
        self.avro_schema = self.generate_avro_schema()
        # Save again to store the schema
        super().save(update_fields=['avro_schema'])

        # Save to SchemaRegistry
        from AvroSchemaManager.models import SchemaRegistry
        registry_name = self.avro_schema.get('name') or f"Form{self.id}"
        registry_namespace = self.avro_schema.get('namespace') or f"{self.name.replace(' ', '_')}.v{self.version}"
        SchemaRegistry.objects.update_or_create(
            name=registry_name,
            version=self.version,
            defaults={
                'namespace': registry_namespace,
                'avro_schema': self.avro_schema,
            }
        )

    def generate_avro_schema(self):
        fields = []
        # Get all questions across all pages in order
        pages = self.pages.all().order_by('submissionformpage__order')
        for page in pages:
            questions = page.questions.all().order_by('formpagequestion__order')
            for question in questions:
                # Use 'q<id>' as field name to match the form input names
                fields.append({
                    "name": f"q{question.id}",
                    "type": ["null", "string"],
                    "default": None,
                    "doc": question.label
                })
        return {
            "type": "record",
            "name": f"Form{self.id}_v{self.version}",
            "namespace": f"{self.name.replace(' ', '_')}.v{self.version}",
            "fields": fields,
        }

    def avro_serialize(self, data):
        schema = self.avro_schema or self.generate_avro_schema()
        # Convert QueryDict or dict to plain dict with expected types
        processed_data = {}
        for field in schema.get('fields', []):
            name = field['name']
            val = data.get(name)
            if isinstance(val, list):
                val = val[0] if val else None
            processed_data[name] = str(val) if val is not None else None

        parsed_schema = fastavro.parse_schema(schema)
        bytes_io = io.BytesIO()
        fastavro.writer(bytes_io, parsed_schema, [processed_data])
        return bytes_io.getvalue()

    def avro_deserialize(self, data):
        """
        Deserializes Avro bytes back into a dictionary using the schema from SchemaRegistry.
        Validates the data against the schema.
        """
        from AvroSchemaManager.models import SchemaRegistry
        
        # Look up the schema in the SchemaRegistry
        registry_name = self.avro_schema.get('name') 
        registry_entry = SchemaRegistry.objects.get(
                name=registry_name,
                version=self.version
            )
        schema = registry_entry.avro_schema

        bytes_io = io.BytesIO(data)
        reader = fastavro.reader(bytes_io)
        # Note: fastavro.reader might use the writer's schema if it's embedded.
        # But we want to ensure it matches the registry's schema.
        records = list(reader)
        
        if records:
            record = records[0]
            # Validate the record against the retrieved schema
            fastavro.validation.validate(record, schema)
            return record, registry_entry
        return {}, None

class FormPageQuestion(models.Model):
    form_page = models.ForeignKey(FormPage, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('form_page', 'order')

class SubmissionFormPage(models.Model):
    submission_form = models.ForeignKey(SubmissionForm, on_delete=models.CASCADE)
    form_page = models.ForeignKey(FormPage, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('submission_form', 'order')


@receiver(post_save, sender=FormPage)
def update_submission_form_schema(sender, instance, **kwargs):
    """
    When a FormPage is saved, we need to trigger a re-save of all related SubmissionForm objects
    to ensure their cached avro_schema is updated.
    """
    related_forms = SubmissionForm.objects.filter(pages=instance)
    for form in related_forms:
        form.save()
