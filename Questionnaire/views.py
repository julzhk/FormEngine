from django.shortcuts import get_object_or_404, redirect, render

from .jinja_env import environment, get_required_fields
from .models import Page, Questionnaire


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

    rendered_content = environment.from_string(page.content).render(
        questionnaire=questionnaire,
        page=page,
        errors=errors,
        data=request.POST
    )

    return render(request, 'questionnaire/page.html', {
        'questionnaire': questionnaire,
        'page': page,
        'rendered_content': rendered_content,
        'errors': errors,
        'data': request.POST, 
    })
