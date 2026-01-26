from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from .models import Question, FormPage, SubmissionForm, FormPageQuestion, SubmissionFormPage
from .processor import PetProcessor
from EventManager.models import Event, ConsumerOffset

class FormComposerModelTest(TestCase):
    def test_form_creation_with_ordering(self):
        # Create Questions
        q1 = Question.objects.create(label="What is your name?")
        q2 = Question.objects.create(label="Where do you live?")

        # Create FormPage
        page1 = FormPage.objects.create(title="Page 1")

        # Connect Questions to Page with order
        FormPageQuestion.objects.create(form_page=page1, question=q1, order=1)
        FormPageQuestion.objects.create(form_page=page1, question=q2, order=2)

        self.assertEqual(page1.questions.count(), 2)
        self.assertEqual(page1.questions.first(), q1)
        self.assertEqual(page1.questions.last(), q2)

        # Create SubmissionForm
        form = SubmissionForm.objects.create(name="User Info Form")

        # Connect Page to Form with order
        SubmissionFormPage.objects.create(submission_form=form, form_page=page1, order=1)

        self.assertEqual(form.pages.count(), 1)
        self.assertEqual(form.pages.first(), page1)

class FormComposerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.q1 = Question.objects.create(label="Question 1")
        self.q2 = Question.objects.create(label="Question 2")
        
        self.page1 = FormPage.objects.create(title="Page 1")
        FormPageQuestion.objects.create(form_page=self.page1, question=self.q1, order=1)
        
        self.page2 = FormPage.objects.create(title="Page 2")
        FormPageQuestion.objects.create(form_page=self.page2, question=self.q2, order=1)
        
        self.form = SubmissionForm.objects.create(name="Multi-page Form")
        SubmissionFormPage.objects.create(submission_form=self.form, form_page=self.page1, order=1)
        SubmissionFormPage.objects.create(submission_form=self.form, form_page=self.page2, order=2)

    def test_form_detail_view_first_page(self):
        response = self.client.get(reverse('form_detail', args=[self.form.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 1")
        self.assertContains(response, "Question 1")
        self.assertContains(response, "Next")
        self.assertNotContains(response, "Previous")

    def test_form_detail_view_second_page(self):
        response = self.client.get(reverse('form_detail', args=[self.form.id]) + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 2")
        self.assertContains(response, "Question 2")
        self.assertContains(response, "Previous")
        self.assertContains(response, "Submit")

    def test_form_detail_view_htmx_request(self):
        response = self.client.get(
            reverse('form_detail', args=[self.form.id]) + "?page=2",
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        # Should only return the partial, not the whole base template
        self.assertNotContains(response, "<!DOCTYPE html>")
        self.assertContains(response, "Page 2")

    def test_submit_form_view(self):
        # We expect a new URL 'submit_form' to exist
        url = reverse('submit_form', args=[self.form.id])
        data = {
            f'q{self.q1.id}': 'Answer 1',
            f'q{self.q2.id}': 'Answer 2',
        }
        
        initial_event_count = Event.objects.count()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "acknowledgement message")
        self.assertContains(response, "queued for processing")
        
        # Verify an event was created
        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        event = Event.objects.last()
        self.assertEqual(event.metadata['form_id'], self.form.id)

    def test_submit_form_with_processor_metadata(self):
        # Set a processor for the form
        self.form.processor_class = 'FormComposer.processor.PetProcessor'
        self.form.save()
        
        url = reverse('submit_form', args=[self.form.id])
        data = {f'q{self.q1.id}': 'test answer'}
        
        initial_event_count = Event.objects.count()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        # Verify an event was created with correct processor class in metadata
        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        event = Event.objects.last()
        self.assertEqual(event.metadata['processor_class'], 'FormComposer.processor.PetProcessor')
        
        # Verify it can be deserialized back
        deserialized = self.form.avro_deserialize(event.data)
        self.assertEqual(deserialized[f'q{self.q1.id}'], 'test answer')

from django.core.management import call_command

class FormComposerManagementCommandTest(TestCase):
    def test_process_events_command(self):
        # Setup form and events
        q1 = Question.objects.create(label="Name")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        form = SubmissionForm.objects.create(
            name="Pet Form", 
            processor_class='FormComposer.processor.PetProcessor'
        )
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        form.save()

        # Create an event
        data1 = {f'q{q1.id}': 'Fido'}
        avro_data1 = form.avro_serialize(data1)
        
        Event.objects.create(
            data=avro_data1,
            metadata={'form_id': form.id, 'processor_class': form.processor_class}
        )
        
        # Call the management command
        with patch.object(PetProcessor, 'do_process') as mock_do_process:
            call_command('process_events')
            
            # Check if do_process was called
            self.assertEqual(mock_do_process.call_count, 1)
            
        # Verify offset is updated
        offset = ConsumerOffset.objects.get(processor_class=form.processor_class)
        self.assertIsNotNone(offset.offset)

class ProcessorTest(TestCase):
    def test_pet_processor(self):
        import os
        import glob
        # Create a form for the processor
        q1 = Question.objects.create(label="Name")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        form = SubmissionForm.objects.create(name="Pet Form")
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        form.save()

        processor = PetProcessor()
        data = {f'q{q1.id}': 'Fido'}
        serialized_data = form.avro_serialize(data)
        
        # This will now use form.avro_deserialize and trigger do_process which writes a file
        processor.process(serialized_data, form)
        
        # Verify it can be instantiated
        self.assertTrue(isinstance(processor, PetProcessor))

        # Check for created file
        files = glob.glob("*.txt")
        self.assertTrue(len(files) > 0)
        
        # Clean up
        found = False
        for f in files:
            with open(f, 'r') as file_content:
                if file_content.read() == 'Fido':
                    os.remove(f)
                    found = True
                    break
        self.assertTrue(found, "The output file with content 'Fido' was not found.")

    def test_pet_processor_consume(self):
        # Setup form and events
        q1 = Question.objects.create(label="Name")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        form = SubmissionForm.objects.create(
            name="Pet Form", 
            processor_class='FormComposer.processor.PetProcessor'
        )
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        form.save()

        # Create two events
        data1 = {f'q{q1.id}': 'Fido'}
        data2 = {f'q{q1.id}': 'Rex'}
        
        avro_data1 = form.avro_serialize(data1)
        avro_data2 = form.avro_serialize(data2)
        
        event1 = Event.objects.create(
            data=avro_data1,
            metadata={'form_id': form.id, 'processor_class': form.processor_class}
        )
        event2 = Event.objects.create(
            data=avro_data2,
            metadata={'form_id': form.id, 'processor_class': form.processor_class}
        )
        
        processor = PetProcessor()
        
        # Initially offset should not exist or be null
        offset = ConsumerOffset.objects.filter(processor_class=form.processor_class).first()
        self.assertTrue(offset is None or offset.offset is None)
        
        # Consume events
        with patch.object(PetProcessor, 'do_process') as mock_do_process:
            PetProcessor.consume()
            
            # Check if do_process was called for both events
            self.assertEqual(mock_do_process.call_count, 2)
            
        # Check if offset is updated to event2
        offset = ConsumerOffset.objects.get(processor_class=form.processor_class)
        self.assertEqual(offset.offset, event2)
        
        # Add another event and consume again
        data3 = {f'q{q1.id}': 'Buddy'}
        avro_data3 = form.avro_serialize(data3)
        event3 = Event.objects.create(
            data=avro_data3,
            metadata={'form_id': form.id, 'processor_class': form.processor_class}
        )
        
        with patch.object(PetProcessor, 'do_process') as mock_do_process:
            PetProcessor.consume()
            self.assertEqual(mock_do_process.call_count, 1)
            
        offset.refresh_from_db()
        self.assertEqual(offset.offset, event3)

    def test_submission_form_avro_deserialize(self):
        q1 = Question.objects.create(label="Name")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        form = SubmissionForm.objects.create(name="Pet Form")
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        form.save()

        data = {f'q{q1.id}': 'Fido'}
        serialized_data = form.avro_serialize(data)
        deserialized_data = form.avro_deserialize(serialized_data)
        
        self.assertEqual(deserialized_data[f'q{q1.id}'], 'Fido')

    def test_submission_form_avro_deserialize_validation_failure(self):
        import fastavro
        import io
        from fastavro.validation import ValidationError
        
        q1 = Question.objects.create(label="Name")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        form = SubmissionForm.objects.create(name="Pet Form")
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        form.save()
        
        # Create data with a different schema that has a DIFFERENT type for the SAME field name
        # OR a missing field that is required.
        # Our schema has fields as ["null", "string"].
        # Let's try to pass an integer to a field that should be a string.
        
        field_name = f'q{q1.id}'
        wrong_schema = {
            "type": "record",
            "name": f"Form{form.id}",
            "fields": [
                {"name": field_name, "type": "int"}
            ]
        }
        
        bytes_io = io.BytesIO()
        fastavro.writer(bytes_io, fastavro.parse_schema(wrong_schema), [{field_name: 123}])
        wrong_data = bytes_io.getvalue()
        
        with self.assertRaises(ValidationError):
            form.avro_deserialize(wrong_data)

    def test_pet_processor_avro_serialize(self):
        import io
        import fastavro
        from .models import Question, FormPage, SubmissionForm, FormPageQuestion, SubmissionFormPage
        
        # Setup form for dynamic schema
        q1 = Question.objects.create(label="Name")
        q2 = Question.objects.create(label="Species")
        page = FormPage.objects.create(title="Page")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        FormPageQuestion.objects.create(form_page=page, question=q2, order=2)
        form = SubmissionForm.objects.create(name="Pet Form")
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)

        processor = PetProcessor()
        # Input data matches the expected q<id> format
        data = {f'q{q1.id}': 'Fido', f'q{q2.id}': 'Dog'}
        
        # Explicitly save form to populate cached avro_schema
        form.save()
        
        serialized_data = form.avro_serialize(data)
        
        # Verify it can be deserialized
        bytes_io = io.BytesIO(serialized_data)
        reader = fastavro.reader(bytes_io)
        deserialized_records = list(reader)
        deserialized_data = deserialized_records[0]
        
        self.assertEqual(deserialized_data[f'q{q1.id}'], 'Fido')
        self.assertEqual(deserialized_data[f'q{q2.id}'], 'Dog')

    def test_submission_form_generate_avro_schema(self):
        q1 = Question.objects.create(label="First Name")
        q2 = Question.objects.create(label="Last Name")
        page = FormPage.objects.create(title="Identity")
        FormPageQuestion.objects.create(form_page=page, question=q1, order=1)
        FormPageQuestion.objects.create(form_page=page, question=q2, order=2)
        form = SubmissionForm.objects.create(name="Schema Test Form")
        SubmissionFormPage.objects.create(submission_form=form, form_page=page, order=1)
        
        # We need to trigger save to populate avro_schema
        # In the test, we just created it and then added the page.
        # Adding to the M2M through model (SubmissionFormPage) won't automatically 
        # trigger save() on the SubmissionForm instance unless we call it.
        form.save()

        schema = form.avro_schema
        
        self.assertEqual(schema['type'], 'record')
        self.assertEqual(schema['name'], f'Form{form.id}')
        self.assertEqual(len(schema['fields']), 2)
        self.assertEqual(schema['fields'][0]['name'], f'q{q1.id}')
        self.assertEqual(schema['fields'][0]['doc'], 'First Name')
        self.assertEqual(schema['fields'][1]['name'], f'q{q2.id}')
        self.assertEqual(schema['fields'][1]['doc'], 'Last Name')

    def test_submission_form_processor_choices(self):
        form = SubmissionForm.objects.create(name="Processor Form")
        field = form._meta.get_field('processor_class')
        choices = field.choices
        if callable(choices):
            choices = choices()
        
        # We expect PetProcessor to be in choices
        # The format we defined is f"{sub.__module__}.{sub.__name__}"
        expected_choice = ('FormComposer.processor.PetProcessor', 'PetProcessor')
        self.assertIn(expected_choice, choices)
