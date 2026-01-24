# Clinexa - Ejemplos de Uso

Este documento proporciona ejemplos prácticos de cómo usar los modelos de Clinexa en diferentes escenarios.

## Tabla de Contenidos

1. [Setup Inicial](#setup-inicial)
2. [Gestión de Clínicas](#gestión-de-clínicas)
3. [Gestión de Usuarios](#gestión-de-usuarios)
4. [Gestión de Pacientes](#gestión-de-pacientes)
5. [Gestión de Tratamientos](#gestión-de-tratamientos)
6. [Disclaimers y Aceptaciones](#disclaimers-y-aceptaciones)
7. [Queries Avanzadas](#queries-avanzadas)
8. [Integraciones con Vistas](#integraciones-con-vistas)

---

## Setup Inicial

### Crear la Primera Clínica

```python
from clinics.models import Clinic
from django.utils import timezone

# Crear clínica
clinic = Clinic.objects.create(
    name="Clínica Salud Integral",
    slug="salud-integral",
    tax_id="20123456789",
    email="contacto@saludintegral.com",
    phone="+51987654321",
    address="Av. Principal 123, Lima, Perú",
    subscription_tier=Clinic.SubscriptionTier.PROFESSIONAL,
    subscription_expires_at=timezone.now() + timezone.timedelta(days=365)
)

print(f"Clínica creada: {clinic.name}")
print(f"URL: {clinic.slug}.clinexa.com")
print(f"Suscripción activa: {clinic.is_subscription_active()}")
```

---

## Gestión de Clínicas

### Activar/Desactivar Clínica

```python
# Desactivar clínica (soft delete)
clinic.is_active = False
clinic.save()

# Reactivar clínica
clinic.is_active = True
clinic.save()
```

### Cambiar Plan de Suscripción

```python
# Upgrade a Enterprise
clinic.subscription_tier = Clinic.SubscriptionTier.ENTERPRISE
clinic.subscription_expires_at = timezone.now() + timezone.timedelta(days=365)
clinic.save()

print(f"Plan actualizado a: {clinic.get_subscription_tier_display()}")
```

### Listar Clínicas Activas

```python
active_clinics = Clinic.objects.filter(is_active=True)

for clinic in active_clinics:
    print(f"{clinic.name} - {clinic.get_subscription_tier_display()}")
```

---

## Gestión de Usuarios

### Crear Administrador de Clínica

```python
from clinics.models import User

admin = User.objects.create_user(
    username="admin@saludintegral.com",
    email="admin@saludintegral.com",
    password="secure_password_123",  # En producción, usar contraseña fuerte
    clinic=clinic,
    role=User.Role.ADMIN,
    first_name="María",
    last_name="Administradora"
)

print(f"Admin creado: {admin.get_full_name()}")
```

### Crear Doctor

```python
doctor = User.objects.create_user(
    username="dr.garcia@saludintegral.com",
    email="dr.garcia@saludintegral.com",
    password="doctor_password",
    clinic=clinic,
    role=User.Role.DOCTOR,
    first_name="Carlos",
    last_name="García",
    phone="+51987654321",
    license_number="CMP-12345",
    specialization="Cardiología"
)

print(f"Doctor creado: {doctor.get_full_name()}")
print(f"Especialidad: {doctor.specialization}")
print(f"Licencia: {doctor.license_number}")
```

### Crear Personal de Staff

```python
staff = User.objects.create_user(
    username="recepcion@saludintegral.com",
    email="recepcion@saludintegral.com",
    password="staff_password",
    clinic=clinic,
    role=User.Role.STAFF,
    first_name="Ana",
    last_name="Recepcionista"
)
```

### Verificar Permisos

```python
# Verificar rol
if doctor.is_doctor():
    print("Usuario es doctor, tiene acceso a registros médicos")

if admin.is_admin():
    print("Usuario es admin, tiene acceso completo")

# Verificar que pertenece a la clínica
if doctor.clinic == clinic:
    print("Usuario pertenece a esta clínica")
```

### Listar Usuarios por Rol

```python
# Todos los doctores de la clínica
doctors = User.objects.filter(
    clinic=clinic,
    role=User.Role.DOCTOR
)

for doc in doctors:
    print(f"Dr. {doc.last_name} - {doc.specialization}")
```

---

## Gestión de Pacientes

### Crear Paciente

```python
from clinics.models import Patient
from datetime import date

patient = Patient.objects.create(
    clinic=clinic,
    first_name="Juan",
    last_name="Pérez",
    id_number="12345678",
    date_of_birth=date(1985, 3, 15),
    gender=Patient.Gender.MALE,
    email="juan.perez@example.com",
    phone="+51987654321",
    address="Calle Los Pinos 123, San Isidro, Lima",

    # Contacto de emergencia
    emergency_contact_name="María Pérez",
    emergency_contact_phone="+51987123456",
    emergency_contact_relationship="Esposa",

    # Información médica
    blood_type=Patient.BloodType.A_POSITIVE,
    allergies="Penicilina, Mariscos",
    medical_notes="Hipertensión controlada con medicación"
)

print(f"Paciente creado: {patient.get_full_name()}")
print(f"Edad: {patient.get_age()} años")
print(f"Tipo de sangre: {patient.get_blood_type_display()}")
```

### Buscar Pacientes

```python
# Por nombre
patients = Patient.objects.filter(
    clinic=clinic,
    first_name__icontains="Juan"
)

# Por número de documento
patient = Patient.objects.get(
    clinic=clinic,
    id_number="12345678"
)

# Pacientes activos
active_patients = Patient.objects.filter(
    clinic=clinic,
    is_active=True
)

# Pacientes con alergias
patients_with_allergies = Patient.objects.filter(
    clinic=clinic,
    is_active=True
).exclude(allergies="")

for patient in patients_with_allergies:
    print(f"{patient.get_full_name()}: {patient.allergies}")
```

### Actualizar Información Médica

```python
patient = Patient.objects.get(clinic=clinic, id_number="12345678")

# Actualizar alergias
patient.allergies = "Penicilina, Mariscos, Polen"
patient.medical_notes += "\n\n2026-01-24: Alergia a polen diagnosticada."
patient.save()

print(f"Paciente actualizado: {patient.get_full_name()}")
```

### Desactivar Paciente (Soft Delete)

```python
patient.is_active = False
patient.save()

# Para reactivar
patient.is_active = True
patient.save()
```

---

## Gestión de Tratamientos

### Crear Catálogo de Tratamientos

```python
from clinics.models import Treatment

# Consulta general
consulta = Treatment.objects.create(
    clinic=clinic,
    code="CONS-GEN-001",
    name="Consulta Médica General",
    description="Consulta médica general de primera vez",
    category=Treatment.Category.CONSULTATION,
    duration_minutes=30,
    price=80.00,
    is_active=True
)

# Electrocardiograma
ecg = Treatment.objects.create(
    clinic=clinic,
    code="DIAG-ECG-001",
    name="Electrocardiograma",
    description="Electrocardiograma en reposo de 12 derivaciones",
    category=Treatment.Category.DIAGNOSTIC,
    duration_minutes=20,
    price=120.00,
    is_active=True
)

# Terapia física
terapia = Treatment.objects.create(
    clinic=clinic,
    code="THER-FIS-001",
    name="Sesión de Terapia Física",
    description="Sesión de terapia física y rehabilitación",
    category=Treatment.Category.THERAPY,
    duration_minutes=45,
    price=60.00,
    is_active=True
)

print(f"Tratamientos creados: {Treatment.objects.filter(clinic=clinic).count()}")
```

### Asignar Tratamiento a Paciente

```python
from clinics.models import PatientTreatment
from datetime import date

# Asignar tratamiento único
assignment = PatientTreatment.objects.create(
    patient=patient,
    treatment=ecg,
    assigned_by=doctor,
    status=PatientTreatment.Status.SCHEDULED,
    start_date=date.today(),
    quantity=1,
    notes="Paciente presenta palpitaciones ocasionales"
)

print(f"Tratamiento asignado: {assignment.treatment.name}")
print(f"Precio total: S/ {assignment.get_total_price()}")
```

### Asignar Paquete de Sesiones

```python
# Asignar 10 sesiones de terapia
terapia_paquete = PatientTreatment.objects.create(
    patient=patient,
    treatment=terapia,
    assigned_by=doctor,
    status=PatientTreatment.Status.SCHEDULED,
    start_date=date.today(),
    quantity=10,
    notes="Rehabilitación post-operatoria de rodilla",
    price_override=50.00  # Descuento por paquete
)

print(f"Paquete de {terapia_paquete.quantity} sesiones")
print(f"Precio por sesión: S/ {terapia_paquete.get_final_price()}")
print(f"Precio total: S/ {terapia_paquete.get_total_price()}")
```

### Actualizar Estado de Tratamiento

```python
# Marcar como en progreso
assignment.status = PatientTreatment.Status.IN_PROGRESS
assignment.save()

# Completar tratamiento
assignment.status = PatientTreatment.Status.COMPLETED
assignment.end_date = date.today()
assignment.notes += "\n\nTratamiento completado exitosamente."
assignment.save()
```

### Listar Tratamientos de un Paciente

```python
# Todos los tratamientos del paciente
patient_treatments = PatientTreatment.objects.filter(
    patient=patient
).select_related('treatment', 'assigned_by')

for pt in patient_treatments:
    print(f"{pt.treatment.name} - {pt.get_status_display()}")
    print(f"  Asignado por: Dr. {pt.assigned_by.last_name}")
    print(f"  Precio: S/ {pt.get_total_price()}")
    print()

# Solo tratamientos activos
active_treatments = PatientTreatment.objects.filter(
    patient=patient,
    status__in=[
        PatientTreatment.Status.SCHEDULED,
        PatientTreatment.Status.IN_PROGRESS
    ]
)
```

---

## Disclaimers y Aceptaciones

### Crear Disclaimer

```python
from clinics.models import Disclaimer
from django.utils import timezone

disclaimer = Disclaimer.objects.create(
    clinic=clinic,
    title="Consentimiento Informado General",
    content="""
    Yo, declaro que he sido informado/a de manera clara y precisa sobre:

    1. La naturaleza del tratamiento médico propuesto
    2. Los riesgos y beneficios asociados
    3. Las alternativas disponibles
    4. Las consecuencias de no realizar el tratamiento

    Autorizo expresamente al personal médico de {clinic_name} a realizar
    los procedimientos necesarios para mi atención médica.

    Firma: ___________________
    Fecha: ___________________
    """,
    category=Disclaimer.Category.GENERAL_CONSENT,
    is_active=True,
    effective_date=timezone.now()
)

print(f"Disclaimer creado: {disclaimer.title} v{disclaimer.version}")
```

### Actualizar Disclaimer (Crear Nueva Versión)

```python
# Desactivar versión anterior
old_disclaimer = Disclaimer.objects.get(
    clinic=clinic,
    category=Disclaimer.Category.GENERAL_CONSENT,
    is_active=True
)
old_disclaimer.is_active = False
old_disclaimer.save()

# Crear nueva versión
new_disclaimer = Disclaimer.objects.create(
    clinic=clinic,
    title="Consentimiento Informado General",
    content="Nuevo texto actualizado según regulaciones 2026...",
    category=Disclaimer.Category.GENERAL_CONSENT,
    is_active=True,
    effective_date=timezone.now()
)

print(f"Nueva versión creada: v{new_disclaimer.version}")
```

### Registrar Aceptación de Disclaimer

```python
from clinics.models import DisclaimerAcceptance

# Obtener el disclaimer activo
active_disclaimer = Disclaimer.objects.get(
    clinic=clinic,
    category=Disclaimer.Category.GENERAL_CONSENT,
    is_active=True
)

# Registrar aceptación
acceptance = DisclaimerAcceptance.objects.create(
    patient=patient,
    disclaimer=active_disclaimer,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    accepted_by_user=doctor,
    signature_data="data:image/png;base64,iVBORw0KGgoAAAANS..."  # Base64 de firma
)

print(f"Aceptación registrada para {patient.get_full_name()}")
print(f"Disclaimer: {acceptance.disclaimer.title} v{acceptance.disclaimer.version}")
print(f"Fecha: {acceptance.accepted_at}")
```

### Invalidar Aceptación

```python
# El paciente retira su consentimiento
acceptance.is_valid = False
acceptance.invalidation_reason = "Paciente solicitó retirar consentimiento el 2026-01-24"
acceptance.invalidated_at = timezone.now()
acceptance.save()

print("Aceptación invalidada correctamente")

# Intentar eliminar (esto fallará)
try:
    acceptance.delete()
except ValueError as e:
    print(f"Error esperado: {e}")
```

### Verificar Aceptaciones de un Paciente

```python
# Todas las aceptaciones válidas del paciente
valid_acceptances = DisclaimerAcceptance.objects.filter(
    patient=patient,
    is_valid=True
).select_related('disclaimer')

for acceptance in valid_acceptances:
    print(f"✓ {acceptance.disclaimer.title} v{acceptance.disclaimer.version}")
    print(f"  Aceptado: {acceptance.accepted_at}")
    print(f"  Presenciado por: {acceptance.accepted_by_user.get_full_name()}")
    print()
```

---

## Queries Avanzadas

### Reporte de Pacientes por Tipo de Sangre

```python
from django.db.models import Count

blood_type_report = Patient.objects.filter(
    clinic=clinic,
    is_active=True
).values('blood_type').annotate(
    count=Count('id')
).order_by('-count')

print("Distribución de tipos de sangre:")
for item in blood_type_report:
    blood_type = dict(Patient.BloodType.choices).get(item['blood_type'])
    print(f"{blood_type}: {item['count']} pacientes")
```

### Reporte de Ingresos por Tratamiento

```python
from django.db.models import Sum, F

revenue_report = PatientTreatment.objects.filter(
    patient__clinic=clinic,
    status=PatientTreatment.Status.COMPLETED
).values(
    'treatment__name'
).annotate(
    total_sessions=Sum('quantity'),
    total_revenue=Sum(F('quantity') * F('treatment__price'))
).order_by('-total_revenue')

print("Ingresos por tipo de tratamiento:")
for item in revenue_report:
    print(f"{item['treatment__name']}:")
    print(f"  Sesiones: {item['total_sessions']}")
    print(f"  Ingresos: S/ {item['total_revenue']}")
    print()
```

### Pacientes con Tratamientos Pendientes

```python
from django.db.models import Q

patients_with_pending = Patient.objects.filter(
    clinic=clinic,
    is_active=True,
    patient_treatments__status__in=[
        PatientTreatment.Status.SCHEDULED,
        PatientTreatment.Status.IN_PROGRESS
    ]
).distinct()

print(f"Pacientes con tratamientos pendientes: {patients_with_pending.count()}")

for patient in patients_with_pending:
    pending = PatientTreatment.objects.filter(
        patient=patient,
        status__in=[
            PatientTreatment.Status.SCHEDULED,
            PatientTreatment.Status.IN_PROGRESS
        ]
    )
    print(f"\n{patient.get_full_name()}:")
    for pt in pending:
        print(f"  - {pt.treatment.name} ({pt.get_status_display()})")
```

---

## Integraciones con Vistas

### Vista de Lista de Pacientes (Django View)

```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from clinics.models import Patient

@login_required
def patient_list(request):
    """Lista de pacientes de la clínica del usuario."""

    # Filtrar por clínica del usuario
    patients = Patient.objects.filter(
        clinic=request.user.clinic,
        is_active=True
    ).order_by('last_name', 'first_name')

    # Búsqueda opcional
    search = request.GET.get('search')
    if search:
        patients = patients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(id_number__icontains=search)
        )

    context = {
        'patients': patients,
        'total_patients': patients.count()
    }

    return render(request, 'patients/list.html', context)
```

### Vista de Detalle de Paciente

```python
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied

@login_required
def patient_detail(request, patient_id):
    """Detalle de un paciente específico."""

    patient = get_object_or_404(Patient, id=patient_id)

    # Verificar que el paciente pertenece a la clínica del usuario
    if patient.clinic != request.user.clinic:
        raise PermissionDenied("No tiene acceso a este paciente")

    # Obtener tratamientos del paciente
    treatments = PatientTreatment.objects.filter(
        patient=patient
    ).select_related('treatment', 'assigned_by')

    # Obtener aceptaciones de disclaimers
    acceptances = DisclaimerAcceptance.objects.filter(
        patient=patient,
        is_valid=True
    ).select_related('disclaimer')

    context = {
        'patient': patient,
        'treatments': treatments,
        'acceptances': acceptances,
        'age': patient.get_age()
    }

    return render(request, 'patients/detail.html', context)
```

### API Endpoint (Django REST Framework)

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from clinics.models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    """API ViewSet para pacientes."""

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtrar pacientes por clínica del usuario."""
        return Patient.objects.filter(
            clinic=self.request.user.clinic,
            is_active=True
        )

    def perform_create(self, serializer):
        """Asignar automáticamente la clínica del usuario."""
        serializer.save(clinic=self.request.user.clinic)
```

---

## Consejos y Mejores Prácticas

### 1. Siempre Verificar Pertenencia al Tenant

```python
# CORRECTO
patient = get_object_or_404(Patient, id=patient_id, clinic=request.user.clinic)

# INCORRECTO (vulnerabilidad de seguridad)
patient = get_object_or_404(Patient, id=patient_id)
```

### 2. Usar Transacciones para Operaciones Complejas

```python
from django.db import transaction

@transaction.atomic
def create_patient_with_treatment(clinic, patient_data, treatment, doctor):
    """Crear paciente y asignar tratamiento en una transacción."""

    # Crear paciente
    patient = Patient.objects.create(clinic=clinic, **patient_data)

    # Asignar tratamiento
    assignment = PatientTreatment.objects.create(
        patient=patient,
        treatment=treatment,
        assigned_by=doctor,
        start_date=date.today()
    )

    return patient, assignment
```

### 3. Optimizar Queries con select_related y prefetch_related

```python
# Optimizado
treatments = PatientTreatment.objects.filter(
    patient__clinic=clinic
).select_related(
    'patient',
    'treatment',
    'assigned_by'
).prefetch_related(
    'patient__disclaimer_acceptances'
)

# Evita múltiples queries a la base de datos
for treatment in treatments:
    print(treatment.patient.get_full_name())  # Sin query adicional
    print(treatment.assigned_by.get_full_name())  # Sin query adicional
```

---

Este documento proporciona una guía práctica para trabajar con Clinexa. Para más información, consulta la documentación completa en [README.md](README.md) y [ARCHITECTURE.md](ARCHITECTURE.md).
