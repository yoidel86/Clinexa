# Clinexa - Roadmap de Extensiones Futuras

## Fase 1: MVP Actual (Implementado)

- [x] Multi-tenancy por clínica
- [x] Gestión de usuarios con roles
- [x] Gestión de pacientes
- [x] Catálogo de tratamientos
- [x] Asignación de tratamientos a pacientes
- [x] Disclaimers versionados
- [x] Registro inmutable de aceptaciones

---

## Fase 2: Facturación y Pagos (3-4 semanas)

### 2.1 Sistema de Facturación

**Modelos a Crear:**

```python
class Invoice(TimeStampedModel):
    """Factura generada para un paciente."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(choices=STATUS_CHOICES)  # DRAFT, SENT, PAID, OVERDUE, CANCELLED
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

class InvoiceItem(TimeStampedModel):
    """Líneas de la factura."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    patient_treatment = models.ForeignKey(PatientTreatment, on_delete=models.PROTECT)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(TimeStampedModel):
    """Pagos recibidos."""
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(choices=METHOD_CHOICES)  # CASH, CARD, TRANSFER, INSURANCE
    reference = models.CharField(max_length=100, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT)
```

**Funcionalidades:**
- Generación automática de facturas desde PatientTreatment
- Aplicación de impuestos según configuración de la clínica
- Envío de facturas por email
- Portal de pago online (integración con Stripe/PayPal)
- Recordatorios automáticos de pagos vencidos
- Reportes de ingresos y cuentas por cobrar

**Integraciones:**
- Stripe para pagos con tarjeta
- Sistemas de facturación electrónica locales (SAT, SUNAT, etc.)

---

### 2.2 Gestión de Suscripciones (Clínicas)

**Modelos a Crear:**

```python
class SubscriptionPlan(TimeStampedModel):
    """Planes de suscripción para clínicas."""
    name = models.CharField(max_length=100)  # Basic, Professional, Enterprise
    tier = models.CharField(max_length=20, choices=Clinic.SubscriptionTier.choices)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField()
    max_patients = models.IntegerField()
    features = models.JSONField()  # Lista de features incluidas

class SubscriptionHistory(TimeStampedModel):
    """Historial de suscripciones de una clínica."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_reference = models.CharField(max_length=100)
```

**Funcionalidades:**
- Portal de facturación para administradores de clínica
- Upgrade/downgrade de planes
- Facturación recurrente automática
- Límites por plan (máx. usuarios, pacientes)
- Suspensión automática por falta de pago

---

## Fase 3: Auditoría y Compliance (2-3 semanas)

### 3.1 Auditoría de Acceso

**Modelos a Crear:**

```python
class AuditLog(models.Model):
    """Registro de todas las acciones en el sistema."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=50)  # CREATE, READ, UPDATE, DELETE
    model_name = models.CharField(max_length=100)
    object_id = models.UUIDField()
    changes = models.JSONField()  # Campos modificados (antes/después)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['clinic', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]
```

**Funcionalidades:**
- Logging automático de todas las operaciones CRUD
- Registro de acceso a información de pacientes (PHI)
- Dashboard de auditoría para administradores
- Exportación de logs para compliance
- Alertas de actividad sospechosa

**Compliance:**
- HIPAA audit trail requirements
- GDPR data access logs
- Retención de logs según regulaciones locales

---

### 3.2 Gestión de Consentimientos Avanzada

**Extensiones a Disclaimer/DisclaimerAcceptance:**

```python
class ConsentTemplate(TimeStampedModel):
    """Plantillas de consentimiento con variables dinámicas."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    template_content = models.TextField()  # Con variables: {{patient.name}}, {{treatment.name}}
    required_for_treatments = models.ManyToManyField(Treatment, blank=True)

class DisclaimerAcceptance(TimeStampedModel):
    # Agregar campos:
    geolocation = models.JSONField(null=True, blank=True)  # Lat/Lon del dispositivo
    device_fingerprint = models.TextField(blank=True)  # ID único del dispositivo
    witness_name = models.CharField(max_length=200, blank=True)  # Testigo presencial
    witness_id = models.CharField(max_length=50, blank=True)  # ID del testigo
    recording_url = models.URLField(blank=True)  # Video de la aceptación (si aplica)
```

**Funcionalidades:**
- Captura de firma digital con stylus/touch
- Verificación de identidad con foto (selfie + ID)
- Geolocalización de la aceptación
- Grabación de video del proceso (opcional)
- Exportación a PDF con firma digital
- Envío automático por email al paciente

---

## Fase 4: Firma Digital y Certificación (2-3 semanas)

### 4.1 Integración con Proveedores de Firma Digital

**Proveedores a Integrar:**
- DocuSign
- Adobe Sign
- HelloSign
- Proveedores locales certificados

**Modelos a Crear:**

```python
class DigitalSignature(TimeStampedModel):
    """Firma digital certificada."""
    disclaimer_acceptance = models.OneToOneField(DisclaimerAcceptance, on_delete=models.PROTECT)
    provider = models.CharField(max_length=50)  # DOCUSIGN, ADOBE, etc.
    signature_id = models.CharField(max_length=200)  # ID en el proveedor
    certificate_url = models.URLField()  # URL del certificado
    certificate_hash = models.CharField(max_length=256)  # Hash SHA-256
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True)
```

**Funcionalidades:**
- Firma electrónica simple
- Firma electrónica avanzada
- Firma electrónica certificada (con CA)
- Timestamping con servidor de tiempo
- Validación de certificados
- Blockchain anchoring para inmutabilidad

---

### 4.2 Generación de Documentos PDF

**Modelos a Crear:**

```python
class GeneratedDocument(TimeStampedModel):
    """Documentos PDF generados."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    document_type = models.CharField(max_length=50)  # CONSENT_FORM, MEDICAL_REPORT, INVOICE
    template = models.ForeignKey('DocumentTemplate', on_delete=models.PROTECT)
    file = models.FileField(upload_to='documents/')
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    hash = models.CharField(max_length=256)  # Para verificar integridad
```

**Funcionalidades:**
- Generación de PDFs con datos dinámicos
- Plantillas personalizables por clínica
- Marca de agua con sello digital
- Cifrado de PDFs sensibles
- Almacenamiento en S3/Azure Blob

---

## Fase 5: Gestión de Citas y Agenda (3-4 semanas)

### 5.1 Sistema de Agendamiento

**Modelos a Crear:**

```python
class Schedule(TimeStampedModel):
    """Horarios de trabajo de doctores."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    doctor = models.ForeignKey(User, on_delete=models.PROTECT)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

class Appointment(TimeStampedModel):
    """Citas médicas."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    doctor = models.ForeignKey(User, on_delete=models.PROTECT)
    treatment = models.ForeignKey(Treatment, on_delete=models.PROTECT, null=True)
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(choices=STATUS_CHOICES)  # SCHEDULED, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW
    notes = models.TextField(blank=True)
    reminder_sent = models.BooleanField(default=False)

class AppointmentNote(TimeStampedModel):
    """Notas clínicas de la cita."""
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT)
    doctor = models.ForeignKey(User, on_delete=models.PROTECT)
    notes = models.TextField()
    diagnosis = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
```

**Funcionalidades:**
- Calendario visual para doctores
- Reserva online para pacientes
- Recordatorios automáticos (SMS/Email/WhatsApp)
- Gestión de cancelaciones y reprogramaciones
- Lista de espera automática
- Sincronización con Google Calendar / Outlook

---

## Fase 6: Historia Clínica Electrónica (4-6 semanas)

### 6.1 Expediente Médico Digital

**Modelos a Crear:**

```python
class MedicalRecord(TimeStampedModel):
    """Expediente médico del paciente."""
    patient = models.OneToOneField(Patient, on_delete=models.PROTECT)
    family_history = models.TextField(blank=True)
    personal_history = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)

class Diagnosis(TimeStampedModel):
    """Diagnósticos del paciente."""
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    appointment = models.ForeignKey('Appointment', on_delete=models.PROTECT, null=True)
    icd10_code = models.CharField(max_length=10)  # Código CIE-10
    description = models.TextField()
    diagnosed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    diagnosed_at = models.DateTimeField()
    is_chronic = models.BooleanField(default=False)

class Prescription(TimeStampedModel):
    """Recetas médicas."""
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    doctor = models.ForeignKey(User, on_delete=models.PROTECT)
    medication = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField()
    prescribed_at = models.DateTimeField()

class LabResult(TimeStampedModel):
    """Resultados de laboratorio."""
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    test_type = models.CharField(max_length=200)
    result = models.TextField()
    file = models.FileField(upload_to='lab_results/', null=True)
    ordered_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ordered_labs')
    performed_at = models.DateTimeField()
```

**Funcionalidades:**
- Visualización cronológica de historial
- Integración con laboratorios externos
- Recetas electrónicas
- Imágenes médicas (DICOM viewer)
- Gráficos de evolución (peso, presión, etc.)

---

## Fase 7: Comunicación y Notificaciones (2-3 semanas)

### 7.1 Sistema de Mensajería

**Modelos a Crear:**

```python
class Message(TimeStampedModel):
    """Mensajes entre usuarios y pacientes."""
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    sender_user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    sender_patient = models.ForeignKey(Patient, on_delete=models.PROTECT, null=True)
    recipient_user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='received_messages')
    recipient_patient = models.ForeignKey(Patient, on_delete=models.PROTECT, null=True, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True)

class Notification(TimeStampedModel):
    """Notificaciones del sistema."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)  # APPOINTMENT_REMINDER, NEW_MESSAGE, PAYMENT_DUE
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True)
```

**Funcionalidades:**
- Chat en tiempo real (WebSockets)
- Notificaciones push (web y móvil)
- Recordatorios automáticos de citas
- Alertas de resultados de laboratorio
- Confirmación de lectura

---

### 7.2 Integración con Canales Externos

**Integraciones:**
- WhatsApp Business API (recordatorios, confirmaciones)
- SMS (Twilio, Vonage)
- Email transaccional (SendGrid, Mailgun)
- Notificaciones push móviles (Firebase)

---

## Fase 8: Reportes y Analytics (2-3 semanas)

### 8.1 Dashboard de Métricas

**Métricas a Implementar:**

**Para Administradores de Clínica:**
- Pacientes nuevos vs recurrentes (mensual)
- Ingresos por tratamiento
- Ocupación de agenda por doctor
- Tiempo promedio de atención
- Tasa de cancelación de citas
- Cuentas por cobrar
- ROI por canal de marketing

**Para Doctores:**
- Pacientes atendidos por período
- Tratamientos más frecuentes
- Tiempo promedio por paciente
- Satisfacción de pacientes (NPS)

**Para Finanzas:**
- Ingresos mensuales/anuales
- Gastos operativos
- Margen por tratamiento
- Proyecciones de flujo de caja

---

### 8.2 Exportación de Datos

**Funcionalidades:**
- Exportación a Excel/CSV
- Reportes PDF personalizados
- Integración con BI tools (Tableau, Power BI)
- API de analytics para integraciones

---

## Fase 9: Seguridad Avanzada (Continuo)

### 9.1 Mejoras de Seguridad

**Implementaciones:**

1. **Cifrado de Datos Sensibles**
   - Cifrado a nivel de campo (django-encrypted-fields)
   - Cifrado de backups
   - Key rotation automática

2. **Autenticación Multi-Factor (2FA)**
   - TOTP (Google Authenticator)
   - SMS
   - Biométrico (para apps móviles)

3. **Control de Acceso Granular**
   - Permisos a nivel de objeto
   - Roles personalizados por clínica
   - Segregación de funciones

4. **Monitoreo de Seguridad**
   - Detección de anomalías
   - Alertas de intentos de acceso sospechosos
   - Bloqueo automático de cuentas

5. **Compliance Automático**
   - Escaneo de vulnerabilidades (OWASP)
   - Análisis de código estático (SonarQube)
   - Penetration testing regular

---

## Fase 10: Integraciones (Variable)

### 10.1 Integraciones con Sistemas Externos

**Prioridad Alta:**
- Sistemas de facturación electrónica (SAT, SUNAT, SRI)
- Aseguradoras médicas
- Laboratorios clínicos
- Farmacias

**Prioridad Media:**
- Pasarelas de pago locales
- Servicios de telemedicina
- Sistemas de radiología (PACS)
- Sistemas hospitalarios (HL7/FHIR)

**Prioridad Baja:**
- Marketing automation (HubSpot, Mailchimp)
- CRM externo (Salesforce)
- Accounting software (QuickBooks, Xero)

---

## Consideraciones de Escalabilidad

### Base de Datos

**Cuando alcanzar 1000+ clínicas:**
- Evaluar sharding por clínica
- Considerar base de datos separada por tenant
- Implementar read replicas
- Particionar tablas grandes (AuditLog)

### Infraestructura

**Escalamiento Horizontal:**
- Contenedores Docker + Kubernetes
- Load balancer con health checks
- Auto-scaling basado en métricas
- CDN para assets estáticos

**Monitoreo:**
- Application Performance Monitoring (New Relic, Datadog)
- Log aggregation (ELK Stack)
- Alertas proactivas

---

## Métricas de Éxito del MVP

**KPIs a Monitorear:**

1. **Adopción:**
   - Clínicas registradas
   - Usuarios activos diarios/mensuales
   - Pacientes registrados por clínica

2. **Engagement:**
   - Tratamientos creados por semana
   - Disclaimers aceptados
   - Tiempo promedio en plataforma

3. **Negocio:**
   - Churn rate de clínicas
   - MRR (Monthly Recurring Revenue)
   - LTV (Lifetime Value) por clínica
   - CAC (Customer Acquisition Cost)

4. **Técnico:**
   - Uptime (objetivo: 99.9%)
   - Response time promedio (objetivo: <200ms)
   - Error rate (objetivo: <0.1%)

---

## Próximos Pasos Inmediatos

1. **Configurar entorno de desarrollo**
   - Docker compose para desarrollo local
   - Base de datos PostgreSQL
   - Redis para caché

2. **Implementar autenticación**
   - JWT tokens para API
   - Session-based para web
   - Middleware de tenant context

3. **Crear fixtures de prueba**
   - Datos de ejemplo para desarrollo
   - Suite de tests automatizados

4. **Implementar Django Admin personalizado**
   - Panel de administración multi-tenant
   - Filtros por clínica automáticos

5. **API REST**
   - Django REST Framework
   - Documentación con Swagger
   - Rate limiting por tenant

Esta roadmap proporciona una guía clara para evolucionar Clinexa desde un MVP hasta una plataforma enterprise robusta y completa.
