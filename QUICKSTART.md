# Clinexa - Guía de Inicio Rápido

Esta guía te ayudará a tener Clinexa funcionando en 5 minutos.

## Prerrequisitos

- Python 3.11+
- PostgreSQL 14+
- pip (gestor de paquetes de Python)

## Instalación Rápida

### 1. Instalar Dependencias

```bash
pip install Django==5.0.1 psycopg2-binary==2.9.9
```

### 2. Configurar Base de Datos

```bash
# Crear base de datos PostgreSQL
createdb clinexa

# O usando psql:
psql -U postgres
CREATE DATABASE clinexa;
\q
```

### 3. Configurar Django

Crear archivo `clinexa_project/settings.py`:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'tu-clave-secreta-aqui-cambiar-en-produccion'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'clinics',  # Nuestra app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clinexa_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinexa_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'clinexa',
        'USER': 'postgres',
        'PASSWORD': 'tu-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_USER_MODEL = 'clinics.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

Crear archivo `clinexa_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
```

Crear archivo `clinexa_project/__init__.py`:

```python
# Archivo vacío
```

Crear archivo `clinexa_project/wsgi.py`:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinexa_project.settings')
application = get_wsgi_application()
```

Crear archivo `manage.py` en la raíz:

```python
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinexa_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)
```

### 4. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear Superusuario

```bash
python manage.py createsuperuser
# Seguir las instrucciones en pantalla
```

### 6. Iniciar Servidor

```bash
python manage.py runserver
```

Acceder a:
- **Aplicación**: http://localhost:8000
- **Admin**: http://localhost:8000/admin

## Primeros Pasos

### 1. Crear tu Primera Clínica

```python
python manage.py shell
```

```python
from clinics.models import Clinic

clinic = Clinic.objects.create(
    name="Mi Clínica",
    slug="mi-clinica",
    tax_id="12345678901",
    email="info@miclinica.com",
    phone="123456789",
    address="Mi Dirección 123"
)

print(f"Clínica creada: {clinic.name}")
```

### 2. Crear un Doctor

```python
from clinics.models import User

doctor = User.objects.create_user(
    username="doctor@miclinica.com",
    email="doctor@miclinica.com",
    password="password123",
    clinic=clinic,
    role=User.Role.DOCTOR,
    first_name="Dr.",
    last_name="Smith"
)

print(f"Doctor creado: {doctor.get_full_name()}")
```

### 3. Crear un Paciente

```python
from clinics.models import Patient
from datetime import date

patient = Patient.objects.create(
    clinic=clinic,
    first_name="Juan",
    last_name="Pérez",
    id_number="12345678",
    date_of_birth=date(1990, 1, 1),
    gender=Patient.Gender.MALE,
    phone="987654321",
    address="Calle 123",
    emergency_contact_name="María Pérez",
    emergency_contact_phone="987123456"
)

print(f"Paciente creado: {patient.get_full_name()}, {patient.get_age()} años")
```

### 4. Crear un Tratamiento

```python
from clinics.models import Treatment

treatment = Treatment.objects.create(
    clinic=clinic,
    code="CONS-001",
    name="Consulta General",
    description="Consulta médica general",
    category=Treatment.Category.CONSULTATION,
    duration_minutes=30,
    price=100.00
)

print(f"Tratamiento creado: {treatment.name} - ${treatment.price}")
```

### 5. Asignar Tratamiento

```python
from clinics.models import PatientTreatment

assignment = PatientTreatment.objects.create(
    patient=patient,
    treatment=treatment,
    assigned_by=doctor,
    status=PatientTreatment.Status.SCHEDULED,
    start_date=date.today(),
    quantity=1
)

print(f"Tratamiento asignado: {assignment.treatment.name}")
print(f"Total: ${assignment.get_total_price()}")
```

## Acceder al Admin

1. Ir a http://localhost:8000/admin
2. Iniciar sesión con el superusuario creado
3. Explorar las secciones:
   - Clinics
   - Users
   - Patients
   - Treatments
   - Patient Treatments
   - Disclaimers
   - Disclaimer Acceptances

## Próximos Pasos

1. **Leer la documentación completa**: [README.md](README.md)
2. **Entender la arquitectura**: [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Ver ejemplos de uso**: [EXAMPLES.md](EXAMPLES.md)
4. **Planificar extensiones**: [ROADMAP.md](ROADMAP.md)

## Estructura de Archivos Creada

```
Clinexa/
├── clinics/                      # Aplicación principal
│   ├── __init__.py
│   ├── models.py                # ✓ Modelos implementados
│   ├── admin.py                 # ✓ Admin configurado
│   ├── managers.py              # ✓ Managers multi-tenant
│   ├── middleware.py            # ✓ Middleware de tenant
│   ├── tests.py                 # ✓ Suite de tests
│   └── migrations/              # Migraciones de BD
│       └── __init__.py
├── clinexa_project/             # Configuración del proyecto
│   ├── __init__.py
│   ├── settings.py              # Configurar según arriba
│   ├── urls.py                  # Configurar según arriba
│   └── wsgi.py                  # Configurar según arriba
├── manage.py                    # Configurar según arriba
├── requirements.txt             # ✓ Dependencias
├── README.md                    # ✓ Documentación principal
├── ARCHITECTURE.md              # ✓ Arquitectura detallada
├── ROADMAP.md                   # ✓ Plan de extensiones
├── EXAMPLES.md                  # ✓ Ejemplos de uso
└── QUICKSTART.md               # ✓ Esta guía
```

## Solución de Problemas

### Error: "No module named 'clinics'"

Verificar que `clinics` está en `INSTALLED_APPS` en `settings.py`.

### Error: "django.db.utils.OperationalError: FATAL: password authentication failed"

Verificar las credenciales de PostgreSQL en `DATABASES` en `settings.py`.

### Error: "AUTH_USER_MODEL refers to model 'clinics.User' that has not been installed"

Ejecutar las migraciones: `python manage.py migrate`

## Soporte

Para más ayuda, consulta la documentación completa o contacta al equipo de desarrollo.

---

**Listo para comenzar a desarrollar tu plataforma de gestión médica!**
