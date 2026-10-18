"""
Django Admin Configuration for Clinexa

This module configures the Django admin interface with multi-tenant
filtering and enhanced usability features.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from .models import (
    Clinic,
    User,
    Patient,
    Treatment,
    PatientTreatment,
    Appointment,
    Disclaimer,
    DisclaimerAcceptance
)


# ============================================================================
# CUSTOM FILTERS
# ============================================================================

class ClinicFilter(admin.SimpleListFilter):
    """Filter to show only active/inactive clinics."""
    title = _('Clinic Status')
    parameter_name = 'clinic_status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active')),
            ('inactive', _('Inactive')),
            ('trial', _('Trial')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)
        if self.value() == 'trial':
            return queryset.filter(subscription_tier='TRIAL')


# ============================================================================
# CLINIC ADMIN
# ============================================================================

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    """Admin interface for Clinic model."""

    list_display = (
        'name',
        'slug',
        'email',
        'subscription_tier',
        'subscription_status',
        'is_active',
        'created_at'
    )
    list_filter = (
        'is_active',
        'subscription_tier',
        'created_at'
    )
    search_fields = (
        'name',
        'slug',
        'email',
        'tax_id'
    )
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'subscription_status'
    )

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'name',
                'slug',
                'tax_id',
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'email',
                'phone',
                'address',
            )
        }),
        (_('Subscription'), {
            'fields': (
                'subscription_tier',
                'subscription_expires_at',
                'is_active',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def subscription_status(self, obj):
        """Display subscription status with color coding."""
        if obj.is_subscription_active():
            return mark_safe('<span style="color: green;">✓ Active</span>')
        return mark_safe('<span style="color: red;">✗ Expired</span>')
    subscription_status.short_description = _('Status')


# ============================================================================
# USER ADMIN
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model with multi-tenant support."""

    list_display = (
        'username',
        'email',
        'get_full_name',
        'clinic',
        'role',
        'is_active',
        'is_staff'
    )
    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'clinic__name',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'clinic__name'
    )
    ordering = ('clinic', 'last_name', 'first_name')
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone'
            )
        }),
        (_('Clinic Association'), {
            'fields': (
                'clinic',
                'role',
            )
        }),
        (_('Professional Credentials'), {
            'fields': (
                'license_number',
                'specialization',
            ),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Clinic Association'), {
            'fields': ('clinic', 'role'),
        }),
    )

    def get_full_name(self, obj):
        """Display user's full name."""
        return obj.get_full_name() or '-'
    get_full_name.short_description = _('Full Name')


# ============================================================================
# PATIENT ADMIN
# ============================================================================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model."""

    list_display = (
        'get_full_name',
        'id_number',
        'clinic',
        'phone',
        'age',
        'is_active',
        'created_at'
    )
    list_filter = (
        'clinic',
        'gender',
        'blood_type',
        'is_active',
        'created_at'
    )
    search_fields = (
        'first_name',
        'last_name',
        'id_number',
        'email',
        'phone'
    )
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'age'
    )

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'clinic',
                'first_name',
                'last_name',
                'id_number',
                'date_of_birth',
                'age',
                'gender',
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'email',
                'phone',
                'address',
            )
        }),
        (_('Emergency Contact'), {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relationship',
            ),
            'classes': ('collapse',)
        }),
        (_('Medical Information'), {
            'fields': (
                'blood_type',
                'allergies',
                'medical_notes',
            ),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def age(self, obj):
        """Display patient's age."""
        return f"{obj.get_age()} years"
    age.short_description = _('Age')


# ============================================================================
# TREATMENT ADMIN
# ============================================================================

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    """Admin interface for Treatment model."""

    list_display = (
        'code',
        'name',
        'clinic',
        'category',
        'price',
        'duration_minutes',
        'is_active'
    )
    list_filter = (
        'clinic',
        'category',
        'is_active',
    )
    search_fields = (
        'code',
        'name',
        'description'
    )
    readonly_fields = (
        'id',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'clinic',
                'code',
                'name',
                'category',
            )
        }),
        (_('Details'), {
            'fields': (
                'description',
                'duration_minutes',
                'price',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# PATIENT TREATMENT ADMIN
# ============================================================================

class AppointmentInline(admin.TabularInline):
    """Inline admin for appointments within PatientTreatment."""
    model = Appointment
    extra = 0
    readonly_fields = ('id', 'created_at')
    fields = (
        'scheduled_date',
        'scheduled_time',
        'status',
        'attended_by',
        'notes'
    )


@admin.register(PatientTreatment)
class PatientTreatmentAdmin(admin.ModelAdmin):
    """Admin interface for PatientTreatment model."""

    list_display = (
        'patient',
        'treatment',
        'assigned_by',
        'status',
        'start_date',
        'end_date',
        'total_sessions',
        'frequency_type',
        'total_price'
    )
    list_filter = (
        'status',
        'frequency_type',
        'start_date',
        'treatment__clinic',
    )
    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'treatment__name',
        'assigned_by__username'
    )
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'total_price',
        'completed_sessions',
        'pending_sessions'
    )
    date_hierarchy = 'start_date'
    inlines = [AppointmentInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'patient',
                'treatment',
                'assigned_by',
            )
        }),
        (_('Schedule'), {
            'fields': (
                'status',
                'start_date',
                'end_date',
            )
        }),
        (_('Sessions & Frequency'), {
            'fields': (
                'total_sessions',
                'completed_sessions',
                'pending_sessions',
                'frequency_type',
                'frequency_interval',
                'preferred_time',
            )
        }),
        (_('Pricing'), {
            'fields': (
                'price_override',
                'total_price',
            )
        }),
        (_('Notes'), {
            'fields': (
                'notes',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['generate_appointments_action']

    def total_price(self, obj):
        """Display total price formatted."""
        return f"${obj.get_total_price():,.2f}"
    total_price.short_description = _('Total Price')

    def completed_sessions(self, obj):
        """Display completed sessions count."""
        return obj.get_completed_sessions()
    completed_sessions.short_description = _('Completed')

    def pending_sessions(self, obj):
        """Display pending sessions count."""
        return obj.get_pending_sessions()
    pending_sessions.short_description = _('Pending')

    @admin.action(description=_('Generate appointments for selected treatments'))
    def generate_appointments_action(self, request, queryset):
        """Generate appointments for selected patient treatments."""
        total_created = 0
        for patient_treatment in queryset:
            appointments = patient_treatment.generate_appointments(save=True)
            total_created += len(appointments)
        self.message_user(
            request,
            f'{total_created} appointments created successfully.'
        )


# ============================================================================
# APPOINTMENT ADMIN
# ============================================================================

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for Appointment model."""

    list_display = (
        'patient_name',
        'treatment_name',
        'scheduled_date',
        'scheduled_time',
        'status',
        'attended_by',
        'clinic_name'
    )
    list_filter = (
        'status',
        'scheduled_date',
        'patient_treatment__patient__clinic',
    )
    search_fields = (
        'patient_treatment__patient__first_name',
        'patient_treatment__patient__last_name',
        'patient_treatment__treatment__name',
        'attended_by__username'
    )
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'patient_name',
        'treatment_name',
        'clinic_name'
    )
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date', 'scheduled_time')

    fieldsets = (
        (_('Appointment Information'), {
            'fields': (
                'id',
                'patient_treatment',
                'patient_name',
                'treatment_name',
                'clinic_name',
            )
        }),
        (_('Schedule'), {
            'fields': (
                'scheduled_date',
                'scheduled_time',
                'duration_minutes',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'attended_by',
            )
        }),
        (_('Actual Timing'), {
            'fields': (
                'actual_start_time',
                'actual_end_time',
            ),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': (
                'notes',
                'cancellation_reason',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_completed', 'mark_as_cancelled', 'mark_as_no_show']

    def patient_name(self, obj):
        """Display patient's full name."""
        return obj.patient.get_full_name()
    patient_name.short_description = _('Patient')

    def treatment_name(self, obj):
        """Display treatment name."""
        return obj.treatment.name
    treatment_name.short_description = _('Treatment')

    def clinic_name(self, obj):
        """Display clinic name."""
        return obj.clinic.name
    clinic_name.short_description = _('Clinic')

    @admin.action(description=_('Mark selected appointments as completed'))
    def mark_as_completed(self, request, queryset):
        """Mark selected appointments as completed."""
        count = queryset.update(status=Appointment.Status.COMPLETED)
        self.message_user(request, f'{count} appointments marked as completed.')

    @admin.action(description=_('Mark selected appointments as cancelled'))
    def mark_as_cancelled(self, request, queryset):
        """Mark selected appointments as cancelled."""
        count = queryset.update(status=Appointment.Status.CANCELLED)
        self.message_user(request, f'{count} appointments marked as cancelled.')

    @admin.action(description=_('Mark selected appointments as no show'))
    def mark_as_no_show(self, request, queryset):
        """Mark selected appointments as no show."""
        count = queryset.update(status=Appointment.Status.NO_SHOW)
        self.message_user(request, f'{count} appointments marked as no show.')


# ============================================================================
# DISCLAIMER ADMIN
# ============================================================================

@admin.register(Disclaimer)
class DisclaimerAdmin(admin.ModelAdmin):
    """Admin interface for Disclaimer model."""

    list_display = (
        'title',
        'clinic',
        'category',
        'version',
        'is_active',
        'effective_date'
    )
    list_filter = (
        'clinic',
        'category',
        'is_active',
        'effective_date',
    )
    search_fields = (
        'title',
        'content'
    )
    readonly_fields = (
        'id',
        'version',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id',
                'clinic',
                'title',
                'category',
                'version',
            )
        }),
        (_('Content'), {
            'fields': (
                'content',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'effective_date',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# DISCLAIMER ACCEPTANCE ADMIN
# ============================================================================

@admin.register(DisclaimerAcceptance)
class DisclaimerAcceptanceAdmin(admin.ModelAdmin):
    """
    Admin interface for DisclaimerAcceptance model.

    NOTE: This is READ-ONLY for compliance reasons.
    Records cannot be modified or deleted.
    """

    list_display = (
        'patient',
        'disclaimer',
        'accepted_at',
        'accepted_by_user',
        'is_valid',
        'validity_status'
    )
    list_filter = (
        'is_valid',
        'accepted_at',
        'patient__clinic',
    )
    search_fields = (
        'patient__first_name',
        'patient__last_name',
        'disclaimer__title'
    )
    readonly_fields = (
        'id',
        'patient',
        'disclaimer',
        'accepted_at',
        'ip_address',
        'user_agent',
        'accepted_by_user',
        'signature_data',
        'created_at',
        'updated_at'
    )
    date_hierarchy = 'accepted_at'

    fieldsets = (
        (_('Acceptance Information'), {
            'fields': (
                'id',
                'patient',
                'disclaimer',
                'accepted_at',
            )
        }),
        (_('Audit Trail'), {
            'fields': (
                'ip_address',
                'user_agent',
                'accepted_by_user',
            )
        }),
        (_('Digital Signature'), {
            'fields': (
                'signature_data',
            ),
            'classes': ('collapse',)
        }),
        (_('Validity'), {
            'fields': (
                'is_valid',
                'invalidation_reason',
                'invalidated_at',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Acceptances should be created through the application, not admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Never allow deletion of acceptance records."""
        return False

    def validity_status(self, obj):
        """Display validity status with color coding."""
        if obj.is_valid:
            return mark_safe('<span style="color: green;">✓ Valid</span>')
        return mark_safe('<span style="color: red;">✗ Invalidated</span>')
    validity_status.short_description = _('Validity')


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = _('Clinexa Administration')
admin.site.site_title = _('Clinexa Admin')
admin.site.index_title = _('Medical Clinic Management System')
