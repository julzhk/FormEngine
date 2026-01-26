from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from .models import Question, FormPage, SubmissionForm, FormPageQuestion, SubmissionFormPage
from .processor import PetProcessor

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
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "acknowledgement message")

    def test_submit_form_with_processor(self):
        # Set a processor for the form
        self.form.processor_class = 'FormComposer.processor.PetProcessor'
        self.form.save()
        
        url = reverse('submit_form', args=[self.form.id])
        data = {'q1': 'test answer'}
        
        with patch('FormComposer.processor.PetProcessor.process') as mock_process:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            mock_process.assert_called_once()
            # The first argument to process is request.POST which is a QueryDict
            args, kwargs = mock_process.call_args
            self.assertEqual(args[0]['q1'], 'test answer')

class ProcessorTest(TestCase):
    def test_pet_processor(self):
        processor = PetProcessor()
        data = {'name': 'Fido', 'species': 'Dog'}
        # This will print to console, which is fine for "logging" as requested
        processor.process(data)
        # We just want to ensure it doesn't crash and follows the interface
        self.assertTrue(isinstance(processor, PetProcessor))

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
