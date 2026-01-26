from django.urls import path
from . import views

urlpatterns = [
    path('form/<int:form_id>/', views.form_detail, name='form_detail'),
    path('form/<int:form_id>/submit/', views.submit_form, name='submit_form'),
]
