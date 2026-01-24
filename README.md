# Clinexa - Multi-Tenant Medical Clinic Management SAAS

Plataforma SAAS para gestión integral de clínicas médicas con arquitectura multi-tenant, diseñada con Django y enfocada en compliance legal, seguridad y escalabilidad.

## Características Principales

- **Multi-Tenancy Robusto**: Aislamiento completo de datos por clínica
- **Gestión de Usuarios**: Sistema de roles (Admin, Doctor, Staff)
- **Gestión de Pacientes**: Expediente completo con información médica
- **Catálogo de Tratamientos**: Servicios ofrecidos por cada clínica
- **Disclaimers Versionados**: Documentos legales con control de versiones
- **Auditoría Inmutable**: Registro legal de aceptación de consentimientos
- **Seguridad First**: Diseñado pensando en HIPAA/GDPR compliance

## Estructura del Proyecto

```
Clinexa/
├── clinics/                    # Aplicación principal
│   ├── models.py              # Modelos de datos
│   ├── admin.py               # Configuración del admin
│   ├── migrations/            # Migraciones de BD
│   └── __init__.py
├── clinexa_project/           # Configuración del proyecto
├── ARCHITECTURE.md            # Documentación de arquitectura
├── ROADMAP.md                # Plan de extensiones futuras
├── README.md                 # Este archivo
└── requirements.txt          # Dependencias Python
```

## Modelos de Datos

### 1. Clinic (Tenant)

Entidad central de la arquitectura multi-tenant. Cada clínica opera de forma independiente.

**Campos clave:**
- UUID como PK (seguridad)
- Slug para subdominios
- Gestión de suscripciones
- Soft-delete con `is_active`

**Uso:**
```python
clinic = Clinic.objects.create(
    name="Clínica Salud Integral",
    slug="salud-integral",
    tax_id="20123456789",
    email="contacto@saludintegral.com",
    phone="+51987654321",
    address="Av. Principal 123, Lima",
    subscription_tier=Clinic.SubscriptionTier.PROFESSIONAL
)
```

### 2. User (Staff)

Usuario interno de la clínica (extiende AbstractUser de Django).

**Roles:**
- `ADMIN`: Gestión completa de la clínica
- `DOCTOR`: Acceso médico completo
- `STAFF`: Acceso limitado (recepción)

**Uso:**
```python
doctor = User.objects.create_user(
    username="dr.smith@saludintegral.com",
    email="dr.smith@saludintegral.com",
    password="secure_password",
    clinic=clinic,
    role=User.Role.DOCTOR,
    first_name="John",
    last_name="Smith",
    license_number="MED-12345",
    specialization="Cardiología"
)
```

### 3. Patient (Paciente)

Paciente registrado en una clínica con información médica completa.

**Información almacenada:**
- Datos personales
- Contacto de emergencia
- Tipo de sangre
- Alergias
- Historia médica

**Uso:**
```python
patient = Patient.objects.create(
    clinic=clinic,
    first_name="María",
    last_name="García",
    id_number="12345678",
    date_of_birth="1990-05-15",
    gender=Patient.Gender.FEMALE,
    email="maria.garcia@example.com",
    phone="+51987654321",
    address="Calle Los Pinos 456",
    emergency_contact_name="Pedro García",
    emergency_contact_phone="+51987123456",
    blood_type=Patient.BloodType.O_POSITIVE,
    allergies="Penicilina, Polen"
)
```

### 4. Treatment (Tratamiento)

Catálogo de servicios médicos ofrecidos por la clínica.

**Categorías:**
- Consulta, Diagnóstico, Procedimiento, Terapia, Cirugía, Emergencia, Preventivo

**Uso:**
```python
treatment = Treatment.objects.create(
    clinic=clinic,
    code="CONS-CARD-01",
    name="Consulta Cardiológica General",
    description="Consulta inicial con cardiólogo",
    category=Treatment.Category.CONSULTATION,
    duration_minutes=45,
    price=150.00
)
```

### 5. PatientTreatment (Asignación)

Relación entre paciente y tratamiento con seguimiento de estado.

**Estados:**
- SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, ON_HOLD

**Uso:**
```python
assignment = PatientTreatment.objects.create(
    patient=patient,
    treatment=treatment,
    assigned_by=doctor,
    status=PatientTreatment.Status.SCHEDULED,
    start_date="2026-02-01",
    quantity=3,  # 3 sesiones
    notes="Control post-operatorio"
)

# Calcular precio total
total = assignment.get_total_price()  # price x quantity
```

### 6. Disclaimer (Documento Legal)

Documentos legales versionados (consentimientos, políticas).

**Principio de versionado:**
- Cada actualización crea una nueva fila
- Versiones antiguas permanecen inmutables
- Solo una versión activa por categoría

**Uso:**
```python
disclaimer = Disclaimer.objects.create(
    clinic=clinic,
    title="Consentimiento Informado General",
    content="Yo, [nombre del paciente], autorizo...",
    category=Disclaimer.Category.GENERAL_CONSENT,
    is_active=True,
    effective_date=timezone.now()
)
# version se auto-incrementa
```

### 7. DisclaimerAcceptance (Aceptación)

Registro legal INMUTABLE de aceptación de disclaimers.

**Características:**
- No permite updates (excepto invalidación)
- No permite deletes
- Auditoría completa (IP, user agent, firma)

**Uso:**
```python
acceptance = DisclaimerAcceptance.objects.create(
    patient=patient,
    disclaimer=disclaimer,
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    accepted_by_user=doctor,
    signature_data="data:image/png;base64,iVBORw0KGgo..."
)

# Para invalidar (no eliminar):
acceptance.is_valid = False
acceptance.invalidation_reason = "Paciente retiró consentimiento"
acceptance.invalidated_at = timezone.now()
acceptance.save()
```

## Instalación

### Requisitos

- Python 3.11+
- PostgreSQL 14+
- Redis 7+ (para caché y Celery)

### Setup Local

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd Clinexa
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

Ejemplo de `.env`:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/clinexa
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. **Configurar base de datos**
```bash
# Crear base de datos en PostgreSQL
createdb clinexa

# Ejecutar migraciones
python manage.py migrate
```

6. **Crear superusuario**
```bash
python manage.py createsuperuser
```

7. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

Acceder a:
- Aplicación: http://localhost:8000
- Admin: http://localhost:8000/admin

## Configuración Multi-Tenant

### Opción 1: Subdomain Routing (Recomendado para Producción)

```python
# settings.py
ALLOWED_HOSTS = ['.clinexa.com']

# middleware/tenant.py
def get_clinic_from_subdomain(request):
    host = request.get_host().split(':')[0]
    subdomain = host.split('.')[0]
    return Clinic.objects.get(slug=subdomain)
```

Ejemplo:
- `salud-integral.clinexa.com` → Clínica "Salud Integral"
- `cardio-center.clinexa.com` → Clínica "Cardio Center"

### Opción 2: Header-Based (Ideal para API)

```python
# middleware/tenant.py
def get_clinic_from_header(request):
    clinic_id = request.headers.get('X-Clinic-ID')
    return Clinic.objects.get(id=clinic_id)
```

### Opción 3: Session-Based (Simple para MVP)

```python
# middleware/tenant.py
def get_clinic_from_session(request):
    if request.user.is_authenticated:
        return request.user.clinic
    return None
```

## Seguridad Multi-Tenant

### Filtrado Automático en Queries

```python
from clinics.managers import TenantManager

class Patient(TimeStampedModel):
    # ... campos ...

    objects = TenantManager()  # Filtra automáticamente por clínica
    all_objects = models.Manager()  # Sin filtro (solo superadmin)

# Uso:
patients = Patient.objects.all()  # Solo pacientes de la clínica actual
all_patients = Patient.all_objects.all()  # Todos los pacientes (cuidado!)
```

### Middleware de Contexto

```python
# settings.py
MIDDLEWARE = [
    # ...
    'clinics.middleware.TenantMiddleware',
]

# En cualquier vista:
from clinics.middleware import get_current_clinic

def my_view(request):
    clinic = get_current_clinic()
    patients = Patient.objects.filter(clinic=clinic)
```

### Row-Level Security (PostgreSQL)

```sql
-- Habilitar RLS en todas las tablas multi-tenant
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatments ENABLE ROW LEVEL SECURITY;

-- Crear política
CREATE POLICY tenant_isolation ON patients
    USING (clinic_id = current_setting('app.current_clinic_id')::uuid);
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=clinics --cov-report=html

# Tests específicos
pytest clinics/tests/test_models.py
```

### Ejemplo de Test

```python
import pytest
from clinics.models import Clinic, Patient

@pytest.mark.django_db
def test_patient_creation():
    clinic = Clinic.objects.create(
        name="Test Clinic",
        slug="test-clinic",
        tax_id="12345678901",
        email="test@clinic.com",
        phone="123456789",
        address="Test Address"
    )

    patient = Patient.objects.create(
        clinic=clinic,
        first_name="John",
        last_name="Doe",
        id_number="87654321",
        date_of_birth="1990-01-01",
        gender=Patient.Gender.MALE,
        phone="987654321",
        address="Patient Address",
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="123123123"
    )

    assert patient.get_full_name() == "John Doe"
    assert patient.get_age() > 0
    assert patient.clinic == clinic
```

## API REST (Próxima Fase)

```python
# Ejemplo de endpoint para tratamientos
GET /api/v1/treatments/
{
    "results": [
        {
            "id": "uuid-here",
            "code": "CONS-CARD-01",
            "name": "Consulta Cardiológica",
            "category": "CONSULTATION",
            "price": 150.00,
            "duration_minutes": 45
        }
    ]
}

# Filtrado automático por clínica del usuario autenticado
```

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "clinexa_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/clinexa
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: clinexa
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

## Mejores Prácticas

### 1. Siempre Filtrar por Clínica

```python
# CORRECTO
patients = Patient.objects.filter(clinic=request.user.clinic)

# INCORRECTO (expone datos de otras clínicas)
patients = Patient.objects.all()
```

### 2. Validar Pertenencia al Tenant

```python
def update_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Validar que el paciente pertenece a la clínica del usuario
    if patient.clinic != request.user.clinic:
        raise PermissionDenied("No tiene acceso a este paciente")

    # ... actualizar paciente
```

### 3. Nunca Modificar DisclaimerAcceptance

```python
# CORRECTO: Invalidar
acceptance.is_valid = False
acceptance.invalidation_reason = "Razón válida"
acceptance.save()

# INCORRECTO: Eliminar
acceptance.delete()  # Lanza ValueError
```

### 4. Usar Transacciones para Operaciones Críticas

```python
from django.db import transaction

@transaction.atomic
def assign_treatment_with_disclaimer(patient, treatment, doctor, disclaimer):
    # Crear asignación
    assignment = PatientTreatment.objects.create(
        patient=patient,
        treatment=treatment,
        assigned_by=doctor,
        status=PatientTreatment.Status.SCHEDULED,
        start_date=timezone.now().date()
    )

    # Registrar aceptación de disclaimer
    acceptance = DisclaimerAcceptance.objects.create(
        patient=patient,
        disclaimer=disclaimer,
        accepted_by_user=doctor
    )

    return assignment, acceptance
```

## Roadmap

Ver [ROADMAP.md](ROADMAP.md) para el plan completo de extensiones futuras:

- **Fase 2**: Facturación y Pagos
- **Fase 3**: Auditoría y Compliance
- **Fase 4**: Firma Digital
- **Fase 5**: Gestión de Citas
- **Fase 6**: Historia Clínica Electrónica
- **Fase 7**: Comunicación y Notificaciones
- **Fase 8**: Reportes y Analytics
- **Fase 9**: Seguridad Avanzada
- **Fase 10**: Integraciones Externas

## Documentación Adicional

- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura detallada del sistema
- [ROADMAP.md](ROADMAP.md) - Plan de desarrollo futuro
- `clinics/models.py` - Modelos con documentación inline completa

## Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Propietario - Todos los derechos reservados

## Soporte

Para preguntas y soporte:
- Email: soporte@clinexa.com
- Documentación: https://docs.clinexa.com

---

**Desarrollado con Django y buenas prácticas de arquitectura de software**
