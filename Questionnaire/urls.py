from django.urls import path

from . import views

app_name = 'questionnaire'

urlpatterns = [
    path('<int:questionnaire_id>/page/<int:page_order>/', views.questionnaire_page, name='page'),
]
