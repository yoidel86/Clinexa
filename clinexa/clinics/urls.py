"""
Clinexa - Clinics Module URLs

URL configuration for the clinics application.
"""

from django.urls import path
from . import views

app_name = 'clinics'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.home_view, name='home'),

    # Patients
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<uuid:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('patients/<uuid:patient_id>/pending-disclaimers/', views.patient_pending_disclaimers_view, name='patient_pending_disclaimers'),

    # Disclaimers
    path('patients/<uuid:patient_id>/disclaimers/<uuid:disclaimer_id>/sign/', views.disclaimer_sign_view, name='disclaimer_sign'),
    path('disclaimers/acceptance/<uuid:acceptance_id>/', views.disclaimer_view_acceptance, name='disclaimer_acceptance'),
]
