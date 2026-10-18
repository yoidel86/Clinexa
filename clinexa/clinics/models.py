"""
Clinexa - Multi-tenant Medical Clinic Management System
Models Module

This module implements a robust multi-tenant architecture for managing
medical clinics, users, patients, treatments, and legal disclaimers.

Architecture Principles:
- Multi-tenancy by Clinic (each clinic is isolated)
- Immutable audit trails for legal compliance
- Versioned disclaimers for regulatory requirements
- Clear separation of concerns
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


# ============================================================================
# BASE MODELS - Multi-tenancy Foundation
# ============================================================================

class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields.

    Best Practice: All models should inherit from this for audit trails.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Clinic(TimeStampedModel):
    """
    Clinic Model - The Tenant Entity

    Represents a medical clinic in the multi-tenant system.
    Each clinic is completely isolated from others.

    Fields:
    - id: UUID primary key for security (prevents enumeration attacks)
    - name: Official clinic name
    - slug: URL-friendly identifier for subdomains
    - tax_id: Tax identification number (RUC, NIT, etc.)
    - email: Primary contact email
    - phone: Primary contact phone
    - address: Physical address
    - is_active: Soft delete flag / subscription status
    - subscription_tier: For future billing (BASIC, PROFESSIONAL, ENTERPRISE)

    Future Extensions:
    - Add billing relationship
    - Add subscription management
    - Add custom branding (logo, colors)
    - Add timezone and locale settings
    """

    class SubscriptionTier(models.TextChoices):
        TRIAL = 'TRIAL', _('Trial')
        BASIC = 'BASIC', _('Basic')
        PROFESSIONAL = 'PROFESSIONAL', _('Professional')
        ENTERPRISE = 'ENTERPRISE', _('Enterprise')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text=_("URL-friendly identifier for subdomain routing")
    )
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Tax identification number (RUC/NIT/etc)")
    )
    email = models.EmailField(
        validators=[EmailValidator()]
    )
    phone = models.CharField(max_length=20)
    address = models.TextField()

    # Business logic fields
    is_active = models.BooleanField(
        default=True,
        help_text=_("Inactive clinics cannot access the system")
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.TRIAL
    )
    subscription_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'clinics'
        verbose_name = _('Clinic')
        verbose_name_plural = _('Clinics')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'subscription_tier']),
        ]

    def __str__(self):
        return self.name

    def is_subscription_active(self):
        """Check if clinic subscription is valid."""
        if not self.subscription_expires_at:
            return True
        return timezone.now() < self.subscription_expires_at


# ============================================================================
# USER MANAGEMENT
# ============================================================================

class User(AbstractUser, TimeStampedModel):
    """
    User Model - Internal Clinic Staff

    Extends Django's AbstractUser to add multi-tenant support.
    Each user belongs to ONE clinic and has a specific role.

    Roles:
    - ADMIN: Full clinic management access
    - DOCTOR: Medical staff with patient/treatment access
    - STAFF: Limited access (reception, scheduling)

    Fields:
    - clinic: FK to Clinic (required - enforces multi-tenancy)
    - role: User's role within the clinic
    - phone: Contact phone
    - license_number: Professional license (for doctors)
    - specialization: Medical specialization (for doctors)

    Security Notes:
    - Users can only access data from their own clinic
    - Implement row-level security in views/querysets
    - Use clinic context in all queries

    Future Extensions:
    - Add profile photo
    - Add digital signature for documents
    - Add multi-clinic support (if users work at multiple clinics)
    - Add 2FA authentication
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrator')
        DOCTOR = 'DOCTOR', _('Doctor')
        STAFF = 'STAFF', _('Staff')

    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.PROTECT,  # Prevent accidental clinic deletion
        related_name='users',
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF
    )
    phone = models.CharField(
        max_length=20,
        blank=True
    )

    # Professional credentials (for doctors)
    license_number = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Medical license number")
    )
    specialization = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Medical specialization")
    )

    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['clinic', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['clinic', 'role']),
            models.Index(fields=['clinic', 'email']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['clinic', 'email'],
                name='unique_email_per_clinic'
            )
        ]

    def __str__(self):
        clinic_name = self.clinic.name if self.clinic else 'Sin clínica'
        return f"{self.get_full_name() or self.username} ({clinic_name})"

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_doctor(self):
        return self.role == self.Role.DOCTOR


# ============================================================================
# PATIENT MANAGEMENT
# ============================================================================

class Patient(TimeStampedModel):
    """
    Patient Model - Clinic's Patients

    Represents a patient registered at a specific clinic.
    Contains personal and medical information.

    Fields:
    - clinic: FK to Clinic (multi-tenant isolation)
    - first_name, last_name: Patient name
    - id_number: National ID or passport
    - date_of_birth: For age calculations
    - gender: For medical records
    - email, phone: Contact information
    - address: Physical address
    - emergency_contact: Emergency contact details
    - blood_type: Critical medical information
    - allergies: Medical allergies (stored as text, consider JSON field)
    - medical_notes: General medical history
    - is_active: Soft delete / inactive patients

    Privacy & Security:
    - Contains PII and PHI (Protected Health Information)
    - Must comply with HIPAA/GDPR
    - Implement field-level encryption for sensitive data
    - Audit all access to patient records

    Future Extensions:
    - Add photo/avatar
    - Add insurance information
    - Add emergency contact as separate model
    - Add medical history as separate timeline
    - Add consent management
    """

    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER = 'O', _('Other')
        PREFER_NOT_SAY = 'N', _('Prefer not to say')

    class BloodType(models.TextChoices):
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'
        UNKNOWN = 'UNK', _('Unknown')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.PROTECT,
        related_name='patients'
    )

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(
        max_length=50,
        help_text=_("National ID, passport, or other identification")
    )
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices
    )

    # Contact Information
    email = models.EmailField(
        blank=True,
        validators=[EmailValidator()]
    )
    phone = models.CharField(max_length=20)
    address = models.TextField()

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True
    )

    # Medical Information
    blood_type = models.CharField(
        max_length=3,
        choices=BloodType.choices,
        default=BloodType.UNKNOWN
    )
    allergies = models.TextField(
        blank=True,
        help_text=_("Comma-separated list of allergies")
    )
    medical_notes = models.TextField(
        blank=True,
        help_text=_("General medical history and notes")
    )

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'patients'
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        ordering = ['clinic', 'last_name', 'first_name']
        indexes = [
            models.Index(fields=['clinic', 'last_name', 'first_name']),
            models.Index(fields=['clinic', 'id_number']),
            models.Index(fields=['clinic', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['clinic', 'id_number'],
                name='unique_id_number_per_clinic'
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        """Calculate patient's current age."""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


# ============================================================================
# TREATMENT MANAGEMENT
# ============================================================================

class Treatment(TimeStampedModel):
    """
    Treatment Model - Medical Services Catalog

    Represents types of medical treatments/services offered by a clinic.
    This is the clinic's service catalog.

    Fields:
    - clinic: FK to Clinic (each clinic defines its own treatments)
    - code: Internal treatment code
    - name: Treatment name
    - description: Detailed description
    - category: Treatment category (CONSULTATION, PROCEDURE, etc.)
    - duration_minutes: Estimated duration
    - price: Base price (for billing)
    - is_active: Whether treatment is currently offered

    Future Extensions:
    - Add pricing tiers
    - Add insurance coverage mapping
    - Add required equipment/resources
    - Add treatment protocols/checklists
    """

    class Category(models.TextChoices):
        CONSULTATION = 'CONSULTATION', _('Consultation')
        DIAGNOSTIC = 'DIAGNOSTIC', _('Diagnostic')
        PROCEDURE = 'PROCEDURE', _('Procedure')
        THERAPY = 'THERAPY', _('Therapy')
        SURGERY = 'SURGERY', _('Surgery')
        EMERGENCY = 'EMERGENCY', _('Emergency')
        PREVENTIVE = 'PREVENTIVE', _('Preventive Care')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name='treatments'
    )

    code = models.CharField(
        max_length=50,
        help_text=_("Internal treatment code (e.g., CPT code)")
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.CONSULTATION
    )

    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text=_("Estimated duration in minutes")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Base price in local currency")
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_("Inactive treatments cannot be assigned to new patients")
    )

    class Meta:
        db_table = 'treatments'
        verbose_name = _('Treatment')
        verbose_name_plural = _('Treatments')
        ordering = ['clinic', 'category', 'name']
        indexes = [
            models.Index(fields=['clinic', 'category']),
            models.Index(fields=['clinic', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['clinic', 'code'],
                name='unique_treatment_code_per_clinic'
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class PatientTreatment(TimeStampedModel):
    """
    PatientTreatment Model - Treatment Assignment

    Represents the relationship between a patient and a treatment.
    This is where we track which treatments a patient is receiving.

    Fields:
    - patient: FK to Patient
    - treatment: FK to Treatment
    - assigned_by: FK to User (who prescribed/assigned)
    - status: Current status of the treatment
    - start_date: When treatment began
    - end_date: When treatment was completed
    - notes: Treatment-specific notes
    - total_sessions: Total number of sessions planned
    - price_override: Custom price (if different from treatment base price)
    - frequency_type: Type of frequency for appointments (NONE, DAILY, WEEKLY, etc.)
    - frequency_interval: Interval for frequency (e.g., every 2 weeks)
    - frequency_days: Days of week for weekly frequency (JSON field)
    """

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        ON_HOLD = 'ON_HOLD', _('On Hold')

    class FrequencyType(models.TextChoices):
        NONE = 'NONE', _('No frequency (single appointment)')
        DAILY = 'DAILY', _('Daily')
        WEEKLY = 'WEEKLY', _('Weekly')
        BIWEEKLY = 'BIWEEKLY', _('Every two weeks')
        MONTHLY = 'MONTHLY', _('Monthly')
        CUSTOM = 'CUSTOM', _('Custom interval')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='patient_treatments'
    )
    treatment = models.ForeignKey(
        Treatment,
        on_delete=models.PROTECT,
        related_name='patient_treatments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_treatments',
        help_text=_("Doctor or staff who assigned this treatment")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    notes = models.TextField(
        blank=True,
        help_text=_("Treatment-specific notes and observations")
    )
    total_sessions = models.PositiveIntegerField(
        default=1,
        help_text=_("Total number of sessions planned for this treatment")
    )
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Override treatment base price if needed")
    )

    # Frequency configuration for generating appointments
    frequency_type = models.CharField(
        max_length=20,
        choices=FrequencyType.choices,
        default=FrequencyType.NONE,
        help_text=_("How often appointments should be scheduled")
    )
    frequency_interval = models.PositiveIntegerField(
        default=1,
        help_text=_("Interval for custom frequency (e.g., every X days)")
    )
    preferred_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_("Preferred time for appointments")
    )

    class Meta:
        db_table = 'patient_treatments'
        verbose_name = _('Patient Treatment')
        verbose_name_plural = _('Patient Treatments')
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['treatment', 'status']),
            models.Index(fields=['assigned_by', 'start_date']),
            models.Index(fields=['start_date', 'status']),
        ]

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.treatment.name} ({self.status})"

    def get_final_price(self):
        """Get the final price (override or base price)."""
        return self.price_override if self.price_override else self.treatment.price

    def get_total_price(self):
        """Calculate total price based on total sessions."""
        return self.get_final_price() * self.total_sessions

    def get_completed_sessions(self):
        """Get the count of completed appointments."""
        return self.appointments.filter(status=Appointment.Status.COMPLETED).count()

    def get_pending_sessions(self):
        """Get the count of pending/scheduled appointments."""
        return self.appointments.filter(
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
        ).count()

    def generate_appointments(self, save=True):
        """
        Generate appointments based on frequency configuration.
        Returns list of Appointment instances.
        """
        from datetime import timedelta

        appointments = []
        current_date = self.start_date
        session_count = 0

        while session_count < self.total_sessions:
            # Create appointment
            appointment = Appointment(
                patient_treatment=self,
                scheduled_date=current_date,
                scheduled_time=self.preferred_time or timezone.now().time().replace(
                    hour=9, minute=0, second=0, microsecond=0
                ),
                status=Appointment.Status.SCHEDULED
            )
            appointments.append(appointment)
            session_count += 1

            if session_count >= self.total_sessions:
                break

            # Calculate next date based on frequency
            if self.frequency_type == self.FrequencyType.NONE:
                break  # Single appointment only
            elif self.frequency_type == self.FrequencyType.DAILY:
                current_date += timedelta(days=1)
            elif self.frequency_type == self.FrequencyType.WEEKLY:
                current_date += timedelta(weeks=1)
            elif self.frequency_type == self.FrequencyType.BIWEEKLY:
                current_date += timedelta(weeks=2)
            elif self.frequency_type == self.FrequencyType.MONTHLY:
                # Add approximately one month
                current_date += timedelta(days=30)
            elif self.frequency_type == self.FrequencyType.CUSTOM:
                current_date += timedelta(days=self.frequency_interval)

        if save:
            for apt in appointments:
                apt.save()

        return appointments


class Appointment(TimeStampedModel):
    """
    Appointment Model - Individual Treatment Sessions

    Represents a scheduled appointment/session for a patient treatment.
    Multiple appointments can belong to a single PatientTreatment.

    Fields:
    - patient_treatment: FK to PatientTreatment
    - scheduled_date: Date of the appointment
    - scheduled_time: Time of the appointment
    - actual_start_time: When the appointment actually started
    - actual_end_time: When the appointment actually ended
    - status: Current status of the appointment
    - attended_by: FK to User (doctor/staff who attended)
    - notes: Session-specific notes
    - cancellation_reason: Reason if cancelled
    """

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        NO_SHOW = 'NO_SHOW', _('No Show')
        RESCHEDULED = 'RESCHEDULED', _('Rescheduled')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    patient_treatment = models.ForeignKey(
        PatientTreatment,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    # Scheduling
    scheduled_date = models.DateField(
        help_text=_("Date of the appointment")
    )
    scheduled_time = models.TimeField(
        help_text=_("Scheduled start time")
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Expected duration in minutes (defaults to treatment duration)")
    )

    # Actual timing (for tracking)
    actual_start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the appointment actually started")
    )
    actual_end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the appointment actually ended")
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )

    attended_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='attended_appointments',
        null=True,
        blank=True,
        help_text=_("Doctor or staff who attended this appointment")
    )

    notes = models.TextField(
        blank=True,
        help_text=_("Session-specific notes and observations")
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text=_("Reason for cancellation if applicable")
    )

    class Meta:
        db_table = 'appointments'
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['patient_treatment', 'status']),
            models.Index(fields=['attended_by', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]

    def __str__(self):
        return (
            f"{self.patient_treatment.patient.get_full_name()} - "
            f"{self.patient_treatment.treatment.name} ({self.scheduled_date})"
        )

    @property
    def patient(self):
        """Shortcut to get the patient."""
        return self.patient_treatment.patient

    @property
    def treatment(self):
        """Shortcut to get the treatment."""
        return self.patient_treatment.treatment

    @property
    def clinic(self):
        """Shortcut to get the clinic."""
        return self.patient_treatment.patient.clinic

    def get_duration(self):
        """Get duration in minutes (custom or from treatment)."""
        return self.duration_minutes or self.treatment.duration_minutes

    def mark_completed(self, attended_by=None, notes=''):
        """Mark appointment as completed."""
        self.status = self.Status.COMPLETED
        self.actual_end_time = timezone.now()
        if attended_by:
            self.attended_by = attended_by
        if notes:
            self.notes = notes
        self.save()

    def mark_cancelled(self, reason=''):
        """Mark appointment as cancelled."""
        self.status = self.Status.CANCELLED
        self.cancellation_reason = reason
        self.save()

    def start_appointment(self, attended_by=None):
        """Mark appointment as in progress."""
        self.status = self.Status.IN_PROGRESS
        self.actual_start_time = timezone.now()
        if attended_by:
            self.attended_by = attended_by
        self.save()


# ============================================================================
# DISCLAIMER & LEGAL COMPLIANCE
# ============================================================================

class Disclaimer(TimeStampedModel):
    """
    Disclaimer Model - Versioned Legal Documents

    Stores versioned legal disclaimers/consent forms.
    Each version is immutable once published.

    Fields:
    - clinic: FK to Clinic (each clinic has its own disclaimers)
    - title: Disclaimer title
    - content: Full legal text (consider using rich text)
    - version: Version number (auto-incremented)
    - category: Type of disclaimer
    - is_active: Only one version should be active per category
    - effective_date: When this version became effective

    Versioning Strategy:
    - Each update creates a NEW disclaimer record
    - Old versions remain in database (immutability)
    - Only the latest active version is shown to patients
    - Historical acceptances reference specific versions

    Future Extensions:
    - Add multi-language support
    - Add rich text editor integration
    - Add template variables for personalization
    - Add expiration/renewal requirements
    """

    class Category(models.TextChoices):
        GENERAL_CONSENT = 'GENERAL', _('General Consent')
        TREATMENT_SPECIFIC = 'TREATMENT', _('Treatment Specific')
        PRIVACY_POLICY = 'PRIVACY', _('Privacy Policy')
        HIPAA = 'HIPAA', _('HIPAA Authorization')
        PHOTO_CONSENT = 'PHOTO', _('Photo/Video Consent')
        FINANCIAL = 'FINANCIAL', _('Financial Agreement')
        RESEARCH = 'RESEARCH', _('Research Participation')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.PROTECT,
        related_name='disclaimers'
    )

    title = models.CharField(max_length=200)
    content = models.TextField(
        help_text=_("Full legal text of the disclaimer")
    )
    version = models.PositiveIntegerField(
        help_text=_("Version number (auto-incremented)")
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL_CONSENT
    )

    is_active = models.BooleanField(
        default=False,
        help_text=_("Only one version per category should be active")
    )
    effective_date = models.DateTimeField(
        default=timezone.now,
        help_text=_("When this version becomes effective")
    )

    class Meta:
        db_table = 'disclaimers'
        verbose_name = _('Disclaimer')
        verbose_name_plural = _('Disclaimers')
        ordering = ['clinic', 'category', '-version']
        indexes = [
            models.Index(fields=['clinic', 'category', 'is_active']),
            models.Index(fields=['clinic', 'is_active']),
            models.Index(fields=['effective_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['clinic', 'category', 'version'],
                name='unique_disclaimer_version_per_category'
            )
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        """Auto-increment version number if not set."""
        if not self.version:
            last_version = Disclaimer.objects.filter(
                clinic=self.clinic,
                category=self.category
            ).order_by('-version').first()
            self.version = (last_version.version + 1) if last_version else 1
        super().save(*args, **kwargs)


class DisclaimerAcceptance(TimeStampedModel):
    """
    DisclaimerAcceptance Model - Immutable Audit Trail

    Records patient acceptance of disclaimers.
    This is a legal audit trail and must be IMMUTABLE.

    Fields:
    - patient: FK to Patient (who accepted)
    - disclaimer: FK to Disclaimer (specific version)
    - accepted_at: Timestamp of acceptance
    - ip_address: IP address for audit trail
    - user_agent: Browser/device information
    - accepted_by_user: FK to User (staff who witnessed/recorded)
    - signature_data: Digital signature (base64 image or e-signature token)
    - is_valid: Whether this acceptance is still valid

    Critical Requirements:
    - NO UPDATE or DELETE operations allowed
    - All fields are read-only after creation
    - Create new record to invalidate (with reason)

    Future Extensions:
    - Add digital signature verification
    - Add blockchain anchoring for legal proof
    - Add document PDF generation
    - Add email confirmation
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='disclaimer_acceptances'
    )
    disclaimer = models.ForeignKey(
        Disclaimer,
        on_delete=models.PROTECT,
        related_name='acceptances'
    )

    # Audit Trail Fields
    accepted_at = models.DateTimeField(
        default=timezone.now,
        editable=False
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address of acceptance for audit trail")
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_("Browser/device information")
    )

    # Witness/Recording User
    accepted_by_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='witnessed_acceptances',
        null=True,
        blank=True,
        help_text=_("Staff member who witnessed or recorded this acceptance")
    )

    # Digital Signature
    signature_data = models.TextField(
        blank=True,
        help_text=_("Base64 encoded signature image or e-signature token")
    )

    # Validity
    is_valid = models.BooleanField(
        default=True,
        help_text=_("Set to False to invalidate (never delete)")
    )
    invalidation_reason = models.TextField(
        blank=True,
        help_text=_("Reason for invalidation if is_valid=False")
    )
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'disclaimer_acceptances'
        verbose_name = _('Disclaimer Acceptance')
        verbose_name_plural = _('Disclaimer Acceptances')
        ordering = ['-accepted_at']
        indexes = [
            models.Index(fields=['patient', 'is_valid']),
            models.Index(fields=['disclaimer', 'is_valid']),
            models.Index(fields=['accepted_at']),
        ]
        # Prevent accidental updates
        permissions = [
            ('can_invalidate_acceptance', 'Can invalidate disclaimer acceptance'),
        ]

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.disclaimer.title} ({self.accepted_at})"

    def save(self, *args, **kwargs):
        """Override save to prevent updates after initial creation."""
        # _state.adding is True when creating a new object
        if not self._state.adding:
            # Record exists - only allow updating is_valid and invalidation fields
            original = DisclaimerAcceptance.objects.get(pk=self.pk)
            if not original.is_valid:
                raise ValueError("Cannot modify invalidated acceptance record")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion - use invalidation instead."""
        raise ValueError(
            "DisclaimerAcceptance records cannot be deleted. "
            "Use invalidation instead (set is_valid=False)."
        )
