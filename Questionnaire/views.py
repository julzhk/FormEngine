from django.shortcuts import get_object_or_404, render

from .jinja_env import environment
from .models import Page, Questionnaire


def questionnaire_page(request, questionnaire_id, page_order):
    if request.method != 'GET':
        print(request.POST)
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id)
    page = get_object_or_404(Page, questionnaire=questionnaire, order=page_order)
    
    context = {
        'questionnaire': questionnaire,
        'page': page,
    }

    rendered_content = environment.from_string(page.content).render(**context)

    return render(request, 'questionnaire/page.html', {
        'questionnaire': questionnaire,
        'page': page,
        'rendered_content': rendered_content,
    })
