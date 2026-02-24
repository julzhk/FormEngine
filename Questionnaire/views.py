import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from EventManager.models import Event
from .jinja_env import get_required_fields, render_page
from .models import Page, Questionnaire, QuestionnaireSubmission


def questionnaire_page(request, questionnaire_id, page_order):
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    page = get_object_or_404(Page, questionnaire=questionnaire, order=page_order)

    errors = []
    if request.method == 'POST':
        required = get_required_fields(page.content)
        errors = [f for f in required if not request.POST.get(f)]
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

