"""
Clinexa - Clinics Module Views

Views for the clinic management interface including:
- Authentication (login/logout)
- Home dashboard with today's appointments
- Disclaimer signing with digital signature
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Exists, OuterRef

from .models import Appointment, Patient, Disclaimer, DisclaimerAcceptance


def login_view(request):
    """
    Handle user login.

    GET: Display login form
    POST: Process login credentials
    """
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect('clinics:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Por favor ingrese usuario y contraseña.')
            return render(request, 'clinics/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                # Check if user's clinic is active
                if user.clinic and not user.clinic.is_active:
                    messages.error(
                        request,
                        'La clínica asociada a su cuenta está inactiva. '
                        'Contacte al administrador.'
                    )
                    return render(request, 'clinics/login.html')

                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}!')

                # Redirect to next URL if provided, otherwise home
                next_url = request.GET.get('next', 'clinics:home')
                return redirect(next_url)
            else:
                messages.error(
                    request,
                    'Su cuenta está desactivada. Contacte al administrador.'
                )
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'clinics/login.html')


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'Ha cerrado sesión exitosamente.')
    return redirect('clinics:login')


@login_required
def home_view(request):
    """
    Home dashboard view.

    Displays:
    - Today's appointments for the user's clinic
    - Quick stats and actions
    """
    user = request.user
    today = timezone.now().date()

    # Get today's appointments for the user's clinic
    appointments_queryset = Appointment.objects.select_related(
        'patient_treatment__patient',
        'patient_treatment__treatment',
        'attended_by'
    )

    # Filter by clinic if user has one
    if user.clinic:
        appointments_queryset = appointments_queryset.filter(
            patient_treatment__patient__clinic=user.clinic
        )

    # Get today's appointments
    todays_appointments = appointments_queryset.filter(
        scheduled_date=today
    ).exclude(
        status__in=[Appointment.Status.CANCELLED, Appointment.Status.RESCHEDULED]
    ).order_by('scheduled_time')

    # Get stats
    total_today = todays_appointments.count()
    completed_today = todays_appointments.filter(
        status=Appointment.Status.COMPLETED
    ).count()
    pending_today = todays_appointments.filter(
        status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
    ).count()
    in_progress = todays_appointments.filter(
        status=Appointment.Status.IN_PROGRESS
    ).count()

    context = {
        'appointments': todays_appointments,
        'today': today,
        'stats': {
            'total': total_today,
            'completed': completed_today,
            'pending': pending_today,
            'in_progress': in_progress,
        }
    }

    return render(request, 'clinics/home.html', context)


# ============================================================================
# PATIENT MANAGEMENT
# ============================================================================

@login_required
def patient_list_view(request):
    """List all patients for the current clinic."""
    user = request.user

    patients = Patient.objects.filter(is_active=True)
    if user.clinic:
        patients = patients.filter(clinic=user.clinic)

    patients = patients.order_by('last_name', 'first_name')

    context = {
        'patients': patients,
    }
    return render(request, 'clinics/patient_list.html', context)


@login_required
def patient_detail_view(request, patient_id):
    """View patient details including disclaimer status."""
    user = request.user

    patient = get_object_or_404(Patient, id=patient_id)

    # Security: Ensure patient belongs to user's clinic
    if user.clinic and patient.clinic != user.clinic:
        messages.error(request, 'No tiene permiso para ver este paciente.')
        return redirect('clinics:patient_list')

    # Get active disclaimers for the clinic
    active_disclaimers = Disclaimer.objects.filter(
        clinic=patient.clinic,
        is_active=True
    )

    # Get patient's acceptances
    acceptances = DisclaimerAcceptance.objects.filter(
        patient=patient,
        is_valid=True
    ).select_related('disclaimer')

    accepted_disclaimer_ids = set(a.disclaimer_id for a in acceptances)

    # Build disclaimer status list
    disclaimer_status = []
    for disclaimer in active_disclaimers:
        acceptance = next(
            (a for a in acceptances if a.disclaimer_id == disclaimer.id),
            None
        )
        disclaimer_status.append({
            'disclaimer': disclaimer,
            'accepted': disclaimer.id in accepted_disclaimer_ids,
            'acceptance': acceptance,
        })

    # Get patient treatments and appointments
    treatments = patient.patient_treatments.select_related(
        'treatment', 'assigned_by'
    ).order_by('-start_date')[:10]

    context = {
        'patient': patient,
        'disclaimer_status': disclaimer_status,
        'treatments': treatments,
        'pending_disclaimers': sum(1 for d in disclaimer_status if not d['accepted']),
    }
    return render(request, 'clinics/patient_detail.html', context)


# ============================================================================
# DISCLAIMER SIGNING
# ============================================================================

@login_required
def disclaimer_sign_view(request, patient_id, disclaimer_id):
    """
    Display disclaimer for patient to sign.

    GET: Show disclaimer content and signature pad
    POST: Process signature and create acceptance record
    """
    user = request.user

    patient = get_object_or_404(Patient, id=patient_id)
    disclaimer = get_object_or_404(Disclaimer, id=disclaimer_id, is_active=True)

    # Security: Ensure patient belongs to user's clinic
    if user.clinic and patient.clinic != user.clinic:
        messages.error(request, 'No tiene permiso para este paciente.')
        return redirect('clinics:home')

    # Check if already signed
    existing_acceptance = DisclaimerAcceptance.objects.filter(
        patient=patient,
        disclaimer=disclaimer,
        is_valid=True
    ).first()

    if existing_acceptance:
        messages.info(request, 'Este disclaimer ya fue firmado por el paciente.')
        return redirect('clinics:patient_detail', patient_id=patient_id)

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data', '')

        if not signature_data:
            messages.error(request, 'Por favor proporcione una firma.')
            return render(request, 'clinics/disclaimer_sign.html', {
                'patient': patient,
                'disclaimer': disclaimer,
            })

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Create acceptance record
        acceptance = DisclaimerAcceptance.objects.create(
            patient=patient,
            disclaimer=disclaimer,
            signature_data=signature_data,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            accepted_by_user=user,
        )

        messages.success(
            request,
            f'Disclaimer "{disclaimer.title}" firmado exitosamente.'
        )
        return redirect('clinics:patient_detail', patient_id=patient_id)

    context = {
        'patient': patient,
        'disclaimer': disclaimer,
    }
    return render(request, 'clinics/disclaimer_sign.html', context)


@login_required
def disclaimer_view_acceptance(request, acceptance_id):
    """View a signed disclaimer acceptance with signature."""
    user = request.user

    acceptance = get_object_or_404(
        DisclaimerAcceptance.objects.select_related('patient', 'disclaimer', 'accepted_by_user'),
        id=acceptance_id
    )

    # Security check
    if user.clinic and acceptance.patient.clinic != user.clinic:
        messages.error(request, 'No tiene permiso para ver este documento.')
        return redirect('clinics:home')

    context = {
        'acceptance': acceptance,
    }
    return render(request, 'clinics/disclaimer_acceptance.html', context)


@login_required
def patient_pending_disclaimers_view(request, patient_id):
    """Get list of pending disclaimers for a patient (AJAX)."""
    patient = get_object_or_404(Patient, id=patient_id)

    # Security check
    if request.user.clinic and patient.clinic != request.user.clinic:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    # Get active disclaimers not yet signed
    signed_disclaimer_ids = DisclaimerAcceptance.objects.filter(
        patient=patient,
        is_valid=True
    ).values_list('disclaimer_id', flat=True)

    pending = Disclaimer.objects.filter(
        clinic=patient.clinic,
        is_active=True
    ).exclude(id__in=signed_disclaimer_ids)

    data = {
        'pending': [
            {
                'id': str(d.id),
                'title': d.title,
                'category': d.get_category_display(),
                'sign_url': f'/clinics/patients/{patient_id}/disclaimers/{d.id}/sign/',
            }
            for d in pending
        ]
    }
    return JsonResponse(data)
