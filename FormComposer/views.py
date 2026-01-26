import importlib
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import SubmissionForm, SubmissionFormPage

def form_detail(request, form_id):
    form = get_object_or_404(SubmissionForm, pk=form_id)
    page_number = int(request.GET.get('page', 1))
    
    # Get the specific page based on order
    form_page_link = SubmissionFormPage.objects.filter(
        submission_form=form, 
        order=page_number
    ).select_related('form_page').first()
    
    if not form_page_link:
        # Handle case where page doesn't exist, maybe show a "Thank you" or first page
        if page_number > 1:
            return render(request, 'FormComposer/completed.html', {'form': form})
        else:
            # If no pages at all
            return render(request, 'FormComposer/no_pages.html', {'form': form})

    form_page = form_page_link.form_page
    questions = form_page.questions.all().order_by('formpagequestion__order')
    
    context = {
        'form': form,
        'form_page': form_page,
        'questions': questions,
        'current_page': page_number,
        'next_page': page_number + 1 if SubmissionFormPage.objects.filter(submission_form=form, order=page_number + 1).exists() else None,
        'prev_page': page_number - 1 if page_number > 1 else None,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'FormComposer/partials/form_page.html', context)
    
    return render(request, 'FormComposer/form_detail.html', context)

def submit_form(request, form_id):
    form = get_object_or_404(SubmissionForm, pk=form_id)
    if request.method == 'POST':
        print(f"Form submission received for form: {form.name} (ID: {form.id})")
        print(f"POST data: {request.POST}")
        
        if form.processor_class:
            try:
                module_path, class_name = form.processor_class.rsplit('.', 1)
                module = importlib.import_module(module_path)
                processor_class = getattr(module, class_name)
                processor = processor_class()
                
                # Convert POST data to Avro serialized data using the cached schema
                avro_data = form.avro_serialize(request.POST)
                
                # Pass the avro data to the process method
                processor.process(avro_data,form)
            except (ImportError, AttributeError, ValueError) as e:
                print(f"Error instantiating or executing processor {form.processor_class}: {e}")

        return HttpResponse('<div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert"><strong class="font-bold">Success!</strong><span class="block sm:inline"> Thank you for your submission. This is an acknowledgement message.</span></div>')
    return HttpResponse("Method not allowed", status=405)
