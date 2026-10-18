"""
Test Suite for Clinexa Multi-Tenant Models

This module contains comprehensive tests for all models,
including multi-tenant isolation and security tests.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from clinics.models import (
    Clinic,
    User,
    Patient,
    Treatment,
    PatientTreatment,
    Disclaimer,
    DisclaimerAcceptance
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def clinic_a(db):
    """Create a test clinic A."""
    return Clinic.objects.create(
        name="Clínica Salud Integral",
        slug="salud-integral",
        tax_id="20123456789",
        email="contacto@saludintegral.com",
        phone="+51987654321",
        address="Av. Principal 123, Lima",
        subscription_tier=Clinic.SubscriptionTier.PROFESSIONAL
    )


@pytest.fixture
def clinic_b(db):
    """Create a test clinic B."""
    return Clinic.objects.create(
        name="Cardio Center",
        slug="cardio-center",
        tax_id="20987654321",
        email="info@cardiocenter.com",
        phone="+51912345678",
        address="Calle Secundaria 456, Lima",
        subscription_tier=Clinic.SubscriptionTier.BASIC
    )


@pytest.fixture
def admin_a(clinic_a):
    """Create an admin user for clinic A."""
    return User.objects.create_user(
        username="admin@saludintegral.com",
        email="admin@saludintegral.com",
        password="secure_password",
        clinic=clinic_a,
        role=User.Role.ADMIN,
        first_name="Admin",
        last_name="User"
    )


@pytest.fixture
def doctor_a(clinic_a):
    """Create a doctor for clinic A."""
    return User.objects.create_user(
        username="dr.smith@saludintegral.com",
        email="dr.smith@saludintegral.com",
        password="secure_password",
        clinic=clinic_a,
        role=User.Role.DOCTOR,
        first_name="John",
        last_name="Smith",
        license_number="MED-12345",
        specialization="Cardiología"
    )


@pytest.fixture
def doctor_b(clinic_b):
    """Create a doctor for clinic B."""
    return User.objects.create_user(
        username="dr.jones@cardiocenter.com",
        email="dr.jones@cardiocenter.com",
        password="secure_password",
        clinic=clinic_b,
        role=User.Role.DOCTOR,
        first_name="Jane",
        last_name="Jones",
        license_number="MED-67890"
    )


@pytest.fixture
def patient_a(clinic_a):
    """Create a patient for clinic A."""
    return Patient.objects.create(
        clinic=clinic_a,
        first_name="María",
        last_name="García",
        id_number="12345678",
        date_of_birth=date(1990, 5, 15),
        gender=Patient.Gender.FEMALE,
        email="maria.garcia@example.com",
        phone="+51987654321",
        address="Calle Los Pinos 456",
        emergency_contact_name="Pedro García",
        emergency_contact_phone="+51987123456",
        blood_type=Patient.BloodType.O_POSITIVE,
        allergies="Penicilina, Polen"
    )


@pytest.fixture
def patient_b(clinic_b):
    """Create a patient for clinic B."""
    return Patient.objects.create(
        clinic=clinic_b,
        first_name="Carlos",
        last_name="Rodríguez",
        id_number="87654321",
        date_of_birth=date(1985, 10, 20),
        gender=Patient.Gender.MALE,
        phone="+51912345678",
        address="Av. Los Olivos 789",
        emergency_contact_name="Ana Rodríguez",
        emergency_contact_phone="+51923456789"
    )


@pytest.fixture
def treatment_a(clinic_a):
    """Create a treatment for clinic A."""
    return Treatment.objects.create(
        clinic=clinic_a,
        code="CONS-CARD-01",
        name="Consulta Cardiológica General",
        description="Consulta inicial con cardiólogo",
        category=Treatment.Category.CONSULTATION,
        duration_minutes=45,
        price=150.00
    )


# ============================================================================
# CLINIC TESTS
# ============================================================================

@pytest.mark.django_db
class TestClinic:
    """Tests for Clinic model."""

    def test_create_clinic(self, clinic_a):
        """Test clinic creation."""
        assert clinic_a.name == "Clínica Salud Integral"
        assert clinic_a.slug == "salud-integral"
        assert clinic_a.is_active is True

    def test_clinic_str(self, clinic_a):
        """Test clinic string representation."""
        assert str(clinic_a) == "Clínica Salud Integral"

    def test_unique_slug(self, clinic_a):
        """Test that slug must be unique."""
        with pytest.raises(IntegrityError):
            Clinic.objects.create(
                name="Another Clinic",
                slug="salud-integral",  # Duplicate slug
                tax_id="20999999999",
                email="other@clinic.com",
                phone="123456789",
                address="Some Address"
            )

    def test_subscription_active(self, clinic_a):
        """Test subscription status check."""
        # No expiration date = always active
        assert clinic_a.is_subscription_active() is True

        # Set future expiration
        clinic_a.subscription_expires_at = timezone.now() + timedelta(days=30)
        clinic_a.save()
        assert clinic_a.is_subscription_active() is True

        # Set past expiration
        clinic_a.subscription_expires_at = timezone.now() - timedelta(days=1)
        clinic_a.save()
        assert clinic_a.is_subscription_active() is False


# ============================================================================
# USER TESTS
# ============================================================================

@pytest.mark.django_db
class TestUser:
    """Tests for User model."""

    def test_create_user(self, doctor_a, clinic_a):
        """Test user creation."""
        assert doctor_a.clinic == clinic_a
        assert doctor_a.role == User.Role.DOCTOR
        assert doctor_a.is_doctor() is True
        assert doctor_a.is_admin() is False

    def test_user_str(self, doctor_a, clinic_a):
        """Test user string representation."""
        assert str(doctor_a) == f"John Smith ({clinic_a.name})"

    def test_unique_email_per_clinic(self, clinic_a, doctor_a):
        """Test that email must be unique per clinic."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="another@saludintegral.com",
                email="dr.smith@saludintegral.com",  # Duplicate
                clinic=clinic_a,
                password="password"
            )

    def test_same_email_different_clinic(self, clinic_a, clinic_b):
        """Test that same email can exist in different clinics."""
        user1 = User.objects.create_user(
            username="doctor@example.com",
            email="doctor@example.com",
            clinic=clinic_a,
            password="password"
        )
        user2 = User.objects.create_user(
            username="doctor2@example.com",
            email="doctor@example.com",  # Same email, different clinic
            clinic=clinic_b,
            password="password"
        )
        assert user1.email == user2.email
        assert user1.clinic != user2.clinic


# ============================================================================
# PATIENT TESTS
# ============================================================================

@pytest.mark.django_db
class TestPatient:
    """Tests for Patient model."""

    def test_create_patient(self, patient_a, clinic_a):
        """Test patient creation."""
        assert patient_a.clinic == clinic_a
        assert patient_a.get_full_name() == "María García"

    def test_patient_age(self, patient_a):
        """Test age calculation."""
        age = patient_a.get_age()
        assert age > 0
        assert age < 150  # Sanity check

    def test_unique_id_number_per_clinic(self, clinic_a, patient_a):
        """Test that id_number must be unique per clinic."""
        with pytest.raises(IntegrityError):
            Patient.objects.create(
                clinic=clinic_a,
                first_name="Another",
                last_name="Patient",
                id_number="12345678",  # Duplicate
                date_of_birth=date(1995, 1, 1),
                gender=Patient.Gender.MALE,
                phone="123456789",
                address="Address",
                emergency_contact_name="Contact",
                emergency_contact_phone="987654321"
            )

    def test_same_id_different_clinic(self, clinic_a, clinic_b):
        """Test that same id_number can exist in different clinics."""
        patient1 = Patient.objects.create(
            clinic=clinic_a,
            first_name="Patient",
            last_name="One",
            id_number="12345678",
            date_of_birth=date(1990, 1, 1),
            gender=Patient.Gender.MALE,
            phone="123456789",
            address="Address",
            emergency_contact_name="Contact",
            emergency_contact_phone="987654321"
        )
        patient2 = Patient.objects.create(
            clinic=clinic_b,
            first_name="Patient",
            last_name="Two",
            id_number="12345678",  # Same ID, different clinic
            date_of_birth=date(1990, 1, 1),
            gender=Patient.Gender.MALE,
            phone="123456789",
            address="Address",
            emergency_contact_name="Contact",
            emergency_contact_phone="987654321"
        )
        assert patient1.id_number == patient2.id_number
        assert patient1.clinic != patient2.clinic


# ============================================================================
# TREATMENT TESTS
# ============================================================================

@pytest.mark.django_db
class TestTreatment:
    """Tests for Treatment model."""

    def test_create_treatment(self, treatment_a, clinic_a):
        """Test treatment creation."""
        assert treatment_a.clinic == clinic_a
        assert treatment_a.price == 150.00

    def test_unique_code_per_clinic(self, clinic_a, treatment_a):
        """Test that treatment code must be unique per clinic."""
        with pytest.raises(IntegrityError):
            Treatment.objects.create(
                clinic=clinic_a,
                code="CONS-CARD-01",  # Duplicate
                name="Another Treatment",
                description="Description",
                price=100.00
            )


# ============================================================================
# PATIENT TREATMENT TESTS
# ============================================================================

@pytest.mark.django_db
class TestPatientTreatment:
    """Tests for PatientTreatment model."""

    def test_create_patient_treatment(self, patient_a, treatment_a, doctor_a):
        """Test patient treatment assignment."""
        assignment = PatientTreatment.objects.create(
            patient=patient_a,
            treatment=treatment_a,
            assigned_by=doctor_a,
            status=PatientTreatment.Status.SCHEDULED,
            start_date=date.today(),
            quantity=3,
            notes="Test notes"
        )
        assert assignment.patient == patient_a
        assert assignment.treatment == treatment_a
        assert assignment.quantity == 3

    def test_price_calculation(self, patient_a, treatment_a, doctor_a):
        """Test price calculation with quantity."""
        assignment = PatientTreatment.objects.create(
            patient=patient_a,
            treatment=treatment_a,
            assigned_by=doctor_a,
            start_date=date.today(),
            quantity=3
        )
        assert assignment.get_final_price() == treatment_a.price
        assert assignment.get_total_price() == treatment_a.price * 3

    def test_price_override(self, patient_a, treatment_a, doctor_a):
        """Test price override functionality."""
        assignment = PatientTreatment.objects.create(
            patient=patient_a,
            treatment=treatment_a,
            assigned_by=doctor_a,
            start_date=date.today(),
            quantity=2,
            price_override=200.00
        )
        assert assignment.get_final_price() == 200.00
        assert assignment.get_total_price() == 400.00


# ============================================================================
# DISCLAIMER TESTS
# ============================================================================

@pytest.mark.django_db
class TestDisclaimer:
    """Tests for Disclaimer model."""

    def test_create_disclaimer(self, clinic_a):
        """Test disclaimer creation with auto-versioning."""
        disclaimer = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento General",
            content="Texto del consentimiento...",
            category=Disclaimer.Category.GENERAL_CONSENT,
            is_active=True
        )
        assert disclaimer.version == 1

    def test_auto_increment_version(self, clinic_a):
        """Test that version auto-increments."""
        # Create first version
        v1 = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Versión 1",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        assert v1.version == 1

        # Create second version
        v2 = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Versión 2",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        assert v2.version == 2

        # Create third version
        v3 = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Versión 3",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        assert v3.version == 3


# ============================================================================
# DISCLAIMER ACCEPTANCE TESTS
# ============================================================================

@pytest.mark.django_db
class TestDisclaimerAcceptance:
    """Tests for DisclaimerAcceptance model."""

    def test_create_acceptance(self, patient_a, clinic_a, doctor_a):
        """Test disclaimer acceptance creation."""
        disclaimer = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Texto",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        acceptance = DisclaimerAcceptance.objects.create(
            patient=patient_a,
            disclaimer=disclaimer,
            ip_address="192.168.1.100",
            accepted_by_user=doctor_a
        )
        assert acceptance.is_valid is True
        assert acceptance.patient == patient_a

    def test_delete_raises_error(self, patient_a, clinic_a, doctor_a):
        """Test that deletion is prevented."""
        disclaimer = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Texto",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        acceptance = DisclaimerAcceptance.objects.create(
            patient=patient_a,
            disclaimer=disclaimer,
            accepted_by_user=doctor_a
        )

        with pytest.raises(ValueError, match="cannot be deleted"):
            acceptance.delete()

    def test_invalidation(self, patient_a, clinic_a, doctor_a):
        """Test invalidation instead of deletion."""
        disclaimer = Disclaimer.objects.create(
            clinic=clinic_a,
            title="Consentimiento",
            content="Texto",
            category=Disclaimer.Category.GENERAL_CONSENT
        )
        acceptance = DisclaimerAcceptance.objects.create(
            patient=patient_a,
            disclaimer=disclaimer,
            accepted_by_user=doctor_a
        )

        # Invalidate
        acceptance.is_valid = False
        acceptance.invalidation_reason = "Paciente retiró consentimiento"
        acceptance.invalidated_at = timezone.now()
        acceptance.save()

        # Verify
        acceptance.refresh_from_db()
        assert acceptance.is_valid is False
        assert acceptance.invalidation_reason != ""


# ============================================================================
# MULTI-TENANT ISOLATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTenantIsolation:
    """Tests to ensure proper tenant isolation."""

    def test_clinic_isolation_patients(self, clinic_a, clinic_b, patient_a, patient_b):
        """Test that clinics cannot access each other's patients."""
        clinic_a_patients = Patient.objects.filter(clinic=clinic_a)
        clinic_b_patients = Patient.objects.filter(clinic=clinic_b)

        assert patient_a in clinic_a_patients
        assert patient_a not in clinic_b_patients
        assert patient_b in clinic_b_patients
        assert patient_b not in clinic_a_patients

    def test_clinic_isolation_users(self, clinic_a, clinic_b, doctor_a, doctor_b):
        """Test that clinics cannot access each other's users."""
        clinic_a_users = User.objects.filter(clinic=clinic_a)
        clinic_b_users = User.objects.filter(clinic=clinic_b)

        assert doctor_a in clinic_a_users
        assert doctor_a not in clinic_b_users
        assert doctor_b in clinic_b_users
        assert doctor_b not in clinic_a_users
