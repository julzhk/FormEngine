import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from EventManager.models import Event
from .jinja_env import get_field_validators, render_page
from .models import Page, Questionnaire, QuestionnaireSubmission


VALIDATORS = {
    "required": lambda value: (False, "This field is required.") if not value else (True, ""),
    "is_number": lambda value: (False, "Please enter a valid number.") if value and not _is_number(value) else (True, ""),
}


def _is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def questionnaire_page(request, questionnaire_id, page_order):
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    page = get_object_or_404(Page, questionnaire=questionnaire, order=page_order)

    errors = []
    error_messages = {}
    if request.method == 'POST':
        field_validators = get_field_validators(page.content)
        for field, validators in field_validators.items():
            value = request.POST.get(field, "")
            for validator_name in validators:
                if validator_name in VALIDATORS:
                    is_valid, error_message = VALIDATORS[validator_name](value)
                    if not is_valid:
                        errors.append(field)
                        error_messages[field] = error_message
                        break

        if not errors:
            next_page = (
                Page.objects
                .filter(questionnaire=questionnaire, order__gt=page_order)
                .order_by('order')
                .first()
            )
            if next_page:
                return redirect('questionnaire:page', questionnaire_id=questionnaire_id, page_order=next_page.order)
            else:
                return redirect('questionnaire:complete', questionnaire_id=questionnaire_id)
            

    rendered_content = render_page(
        page.content,
        errors=errors,
        error_messages=error_messages,
        questionnaire=questionnaire,
        page=page,
        data=request.POST,
    )

    return render(request, 'questionnaire/page.html', {
        'questionnaire': questionnaire,
        'page': page,
        'rendered_content': rendered_content,
        'errors': errors,
        'data': request.POST, 
    })


def questionnaire_complete(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    return render(request, 'questionnaire/complete.html', {
        'questionnaire': questionnaire,
    })


@require_POST
def questionnaire_submit(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    try:
        responses = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    submission = QuestionnaireSubmission.objects.create(
        questionnaire=questionnaire,
        responses=responses,
    )
    Event.objects.create(
        data=responses,
        metadata={
            'source': 'questionnaire',
            'questionnaire_id': questionnaire.pk,
            'questionnaire_name': questionnaire.name,
            'submission_id': submission.pk,
        },
    )
    return JsonResponse({'id': submission.pk})

