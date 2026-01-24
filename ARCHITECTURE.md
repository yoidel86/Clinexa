# Clinexa - Arquitectura Multi-Tenant SAAS

## Resumen Ejecutivo

Clinexa es una plataforma SAAS para gestión de clínicas médicas diseñada con arquitectura multi-tenant. Cada clínica opera de forma completamente aislada, con sus propios usuarios, pacientes, tratamientos y documentos legales.

## Decisiones de Arquitectura

### 1. Multi-Tenancy por Clínica

**Estrategia Implementada: Shared Database, Shared Schema**

Todos los datos de todas las clínicas se almacenan en la misma base de datos y esquema, pero cada tabla incluye una columna `clinic_id` para el filtrado por tenant.

**Ventajas:**
- Costos reducidos de infraestructura
- Mantenimiento simplificado (una sola base de datos)
- Ideal para MVP y escalamiento inicial
- Migraciones más sencillas

**Consideraciones de Seguridad:**
- Implementar Row-Level Security (RLS) en PostgreSQL
- Middleware de Django para inyectar automáticamente filtros por clínica
- Validación estricta en todas las queries
- Auditoría de acceso cross-tenant

### 2. Modelo de Datos

#### Jerarquía de Entidades

```
Clinic (Tenant Root)
├── Users (Staff interno)
├── Patients (Pacientes)
├── Treatments (Catálogo de servicios)
└── Disclaimers (Documentos legales versionados)

Patient
└── PatientTreatments (Tratamientos asignados)
    └── DisclaimerAcceptances (Aceptaciones legales)
```

#### Explicación de Cada Modelo

##### **Clinic** - La Entidad Tenant

El modelo central de la arquitectura multi-tenant. Cada clínica es completamente independiente.

**Campos Clave:**
- `id`: UUID para evitar ataques de enumeración
- `slug`: Identificador para subdominio (ej: `clinica-salud.clinexa.com`)
- `subscription_tier`: Gestión de planes (TRIAL, BASIC, PROFESSIONAL, ENTERPRISE)
- `is_active`: Soft-delete y control de suscripciones vencidas

**Casos de Uso:**
- Onboarding de nuevas clínicas
- Gestión de facturación y suscripciones
- Aislamiento de datos entre tenants

---

##### **User** - Usuarios Internos de la Clínica

Extiende `AbstractUser` de Django para gestionar el personal de la clínica.

**Roles Implementados:**
- `ADMIN`: Acceso completo a la gestión de la clínica
- `DOCTOR`: Acceso a pacientes, tratamientos y registros médicos
- `STAFF`: Acceso limitado (recepción, agendamiento)

**Campos Clave:**
- `clinic`: FK obligatoria - cada usuario pertenece a UNA clínica
- `role`: Control de permisos basado en rol
- `license_number`: Número de licencia médica (para doctores)
- `specialization`: Especialización médica

**Seguridad Multi-Tenant:**
```python
# Ejemplo de filtrado seguro
def get_clinic_users(clinic):
    return User.objects.filter(clinic=clinic)

# NUNCA hacer esto:
User.objects.all()  # Expone usuarios de todas las clínicas
```

---

##### **Patient** - Pacientes de la Clínica

Almacena información personal y médica de los pacientes.

**Campos Críticos:**
- `id_number`: Identificador único por clínica (DNI, pasaporte)
- `blood_type`: Información crítica para emergencias
- `allergies`: Alergias médicas
- `emergency_contact_*`: Contacto de emergencia

**Compliance:**
- Contiene PHI (Protected Health Information)
- Requiere cifrado a nivel de campo para datos sensibles
- Auditoría obligatoria de todos los accesos
- Backup con retención según regulaciones locales

**Constraint de Unicidad:**
```python
# Un paciente puede estar en múltiples clínicas con el mismo ID
UniqueConstraint(fields=['clinic', 'id_number'])
```

---

##### **Treatment** - Catálogo de Servicios

Define los tratamientos/servicios que ofrece cada clínica.

**Categorías:**
- CONSULTATION, DIAGNOSTIC, PROCEDURE, THERAPY, SURGERY, EMERGENCY, PREVENTIVE

**Campos Clave:**
- `code`: Código interno (ej: CPT code para facturación)
- `price`: Precio base del tratamiento
- `duration_minutes`: Para gestión de agenda

**Uso:**
- Catálogo de servicios de la clínica
- Base para facturación
- Estimación de duración de citas

---

##### **PatientTreatment** - Asignación de Tratamientos

Tabla de relación entre Patient y Treatment que registra los tratamientos asignados.

**Estados del Tratamiento:**
- SCHEDULED: Agendado
- IN_PROGRESS: En progreso
- COMPLETED: Completado
- CANCELLED: Cancelado
- ON_HOLD: En espera

**Campos Importantes:**
- `assigned_by`: Usuario que asignó el tratamiento (trazabilidad)
- `price_override`: Permite precios personalizados
- `quantity`: Número de sesiones

**Lógica de Negocio:**
```python
def get_total_price(self):
    return (self.price_override or self.treatment.price) * self.quantity
```

---

##### **Disclaimer** - Documentos Legales Versionados

Almacena versiones de documentos legales (consentimientos, políticas de privacidad, etc.).

**Principio de Versionado:**
- Cada cambio crea una NUEVA fila (inmutabilidad)
- Las versiones antiguas nunca se modifican ni eliminan
- Solo una versión puede estar `is_active=True` por categoría

**Categorías:**
- GENERAL_CONSENT: Consentimiento general
- TREATMENT_SPECIFIC: Consentimiento específico de tratamiento
- PRIVACY_POLICY: Política de privacidad
- HIPAA: Autorización HIPAA
- PHOTO_CONSENT: Consentimiento de fotos/videos
- FINANCIAL: Acuerdo financiero

**Ejemplo de Versionado:**
```
Disclaimer v1 (is_active=False) - 2024-01-01
Disclaimer v2 (is_active=False) - 2024-06-01
Disclaimer v3 (is_active=True)  - 2025-01-01 <- Versión actual
```

---

##### **DisclaimerAcceptance** - Registro de Aceptación (INMUTABLE)

Registro de auditoría legal de aceptaciones de disclaimers por pacientes.

**Principio Fundamental: INMUTABILIDAD**

Este modelo NO permite:
- Actualizaciones (excepto invalidación)
- Eliminaciones (soft-delete mediante `is_valid=False`)

**Campos de Auditoría:**
- `accepted_at`: Timestamp exacto
- `ip_address`: IP del usuario (prueba de aceptación)
- `user_agent`: Navegador/dispositivo
- `accepted_by_user`: Staff que presenció la aceptación
- `signature_data`: Firma digital (base64)

**Invalidación en Lugar de Eliminación:**
```python
# CORRECTO: Invalidar un registro
acceptance.is_valid = False
acceptance.invalidation_reason = "Paciente retiró consentimiento"
acceptance.invalidated_at = timezone.now()
acceptance.save()

# INCORRECTO: Eliminar
acceptance.delete()  # Lanza ValueError
```

**Compliance Legal:**
- Registro inmutable para auditorías legales
- Prueba de consentimiento informado
- Trazabilidad completa de quién, cuándo y cómo

---

## Implementación de Seguridad Multi-Tenant

### Middleware de Tenant Context

```python
# middleware/tenant.py
from threading import local

_thread_locals = local()

def get_current_clinic():
    return getattr(_thread_locals, 'clinic', None)

def set_current_clinic(clinic):
    _thread_locals.clinic = clinic

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extraer clínica del subdominio o header
        clinic = self.get_clinic_from_request(request)
        set_current_clinic(clinic)
        response = self.get_response(request)
        return response

    def get_clinic_from_request(self, request):
        # Opción 1: Subdomain routing
        # subdomain = request.get_host().split('.')[0]
        # return Clinic.objects.get(slug=subdomain)

        # Opción 2: Header-based (para API)
        # clinic_id = request.headers.get('X-Clinic-ID')
        # return Clinic.objects.get(id=clinic_id)

        # Opción 3: Session-based
        return request.user.clinic if request.user.is_authenticated else None
```

### Manager con Filtrado Automático

```python
# managers.py
from django.db import models

class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        clinic = get_current_clinic()
        if clinic:
            return qs.filter(clinic=clinic)
        return qs

# En los modelos:
class Patient(TimeStampedModel):
    # ... campos ...

    objects = TenantManager()  # Filtrado automático
    all_objects = models.Manager()  # Sin filtro (solo para superadmin)
```

### Row-Level Security en PostgreSQL

```sql
-- Habilitar RLS
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Política de acceso
CREATE POLICY tenant_isolation_policy ON patients
    USING (clinic_id = current_setting('app.current_clinic_id')::uuid);
```

---

## Índices y Optimizaciones

### Índices Críticos Implementados

```python
# Todos los modelos multi-tenant
indexes = [
    models.Index(fields=['clinic', 'campo_busqueda']),  # Queries filtradas
]

# Búsquedas frecuentes
indexes = [
    models.Index(fields=['clinic', 'last_name', 'first_name']),  # Pacientes
    models.Index(fields=['clinic', 'is_active']),  # Filtros de estado
]

# Auditoría y compliance
indexes = [
    models.Index(fields=['accepted_at']),  # DisclaimerAcceptance
    models.Index(fields=['patient', 'is_valid']),  # Validaciones
]
```

### Estrategias de Caché

```python
# Cache por clínica
from django.core.cache import cache

def get_clinic_treatments(clinic_id):
    cache_key = f'clinic:{clinic_id}:treatments'
    treatments = cache.get(cache_key)
    if not treatments:
        treatments = Treatment.objects.filter(
            clinic_id=clinic_id,
            is_active=True
        )
        cache.set(cache_key, treatments, 3600)  # 1 hora
    return treatments
```

---

## Migraciones Iniciales

```bash
# Crear migraciones
python manage.py makemigrations clinics

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (requiere ajustes por multi-tenancy)
python manage.py createsuperuser
```

---

## Testing

### Fixtures para Multi-Tenancy

```python
# tests/fixtures.py
import pytest
from clinics.models import Clinic, User

@pytest.fixture
def clinic_a():
    return Clinic.objects.create(
        name="Clínica Salud",
        slug="salud",
        tax_id="20123456789",
        email="info@salud.com",
        phone="123456789",
        address="Av. Principal 123"
    )

@pytest.fixture
def doctor_a(clinic_a):
    return User.objects.create_user(
        username="doctor@salud.com",
        email="doctor@salud.com",
        clinic=clinic_a,
        role=User.Role.DOCTOR,
        license_number="MED-12345"
    )
```

### Test de Aislamiento de Tenant

```python
def test_tenant_isolation(clinic_a, clinic_b, patient_a, patient_b):
    """Verificar que las clínicas no pueden acceder a datos de otras."""

    # Patient A pertenece a Clinic A
    assert patient_a.clinic == clinic_a

    # Filtrar pacientes de Clinic A
    patients = Patient.objects.filter(clinic=clinic_a)

    # Solo debe retornar pacientes de Clinic A
    assert patient_a in patients
    assert patient_b not in patients
```

---

## Conclusión

Esta arquitectura proporciona:

- **Aislamiento robusto** entre clínicas
- **Escalabilidad** para crecimiento del negocio
- **Compliance legal** con auditoría inmutable
- **Flexibilidad** para extensiones futuras
- **Seguridad** multi-capa para datos médicos sensibles

La implementación sigue las mejores prácticas de Django y está lista para ser un MVP que pueda evolucionar hacia un producto enterprise.
