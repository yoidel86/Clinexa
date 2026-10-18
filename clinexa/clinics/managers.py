"""
Custom Django Model Managers for Multi-Tenant Architecture

This module provides custom managers that automatically filter
querysets by the current tenant (clinic) context.
"""

from django.db import models
from threading import local

# Thread-local storage for tenant context
_thread_locals = local()


def get_current_clinic():
    """
    Get the current clinic from thread-local storage.

    Returns:
        Clinic instance or None if no clinic is set in context.
    """
    return getattr(_thread_locals, 'clinic', None)


def set_current_clinic(clinic):
    """
    Set the current clinic in thread-local storage.

    Args:
        clinic: Clinic instance to set as current context.
    """
    _thread_locals.clinic = clinic


def clear_current_clinic():
    """Clear the current clinic from thread-local storage."""
    if hasattr(_thread_locals, 'clinic'):
        delattr(_thread_locals, 'clinic')


class TenantManager(models.Manager):
    """
    Custom manager that automatically filters querysets by current clinic.

    Usage:
        class Patient(TimeStampedModel):
            clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
            # ... other fields ...

            objects = TenantManager()  # Auto-filtered by clinic
            all_objects = models.Manager()  # Unfiltered (admin only)

    Security Note:
        Always use this manager for models that belong to a clinic
        to prevent cross-tenant data leakage.
    """

    def get_queryset(self):
        """
        Override get_queryset to automatically filter by current clinic.

        Returns:
            QuerySet filtered by current clinic if one is set,
            otherwise returns unfiltered queryset.
        """
        queryset = super().get_queryset()
        clinic = get_current_clinic()

        if clinic is not None:
            # Filter by current clinic
            return queryset.filter(clinic=clinic)

        # No clinic in context - return all (be careful!)
        return queryset


class TenantManagerStrict(models.Manager):
    """
    Strict version of TenantManager that raises an error if no clinic is set.

    This is more secure as it prevents accidental queries without clinic context.

    Usage:
        class SensitiveModel(TimeStampedModel):
            clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
            # ... other fields ...

            objects = TenantManagerStrict()  # Requires clinic context
            all_objects = models.Manager()  # Unfiltered (admin only)
    """

    def get_queryset(self):
        """
        Override get_queryset to require a clinic context.

        Returns:
            QuerySet filtered by current clinic.

        Raises:
            ValueError: If no clinic is set in the current context.
        """
        queryset = super().get_queryset()
        clinic = get_current_clinic()

        if clinic is None:
            raise ValueError(
                "No clinic set in current context. "
                "Use set_current_clinic() before querying, "
                "or use all_objects manager for admin operations."
            )

        return queryset.filter(clinic=clinic)


class ActiveTenantManager(TenantManager):
    """
    Manager that filters by current clinic AND active status.

    Usage:
        class Patient(TimeStampedModel):
            clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
            is_active = models.BooleanField(default=True)
            # ... other fields ...

            objects = ActiveTenantManager()  # Active patients in clinic
            all_objects = models.Manager()  # All patients (admin)
    """

    def get_queryset(self):
        """
        Filter by clinic and is_active=True.

        Returns:
            QuerySet filtered by current clinic and active status.
        """
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)


# Example usage in models:
"""
from django.db import models
from .managers import TenantManager, get_current_clinic, set_current_clinic

class Patient(TimeStampedModel):
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    # ... other fields ...
    is_active = models.BooleanField(default=True)

    # Use TenantManager for automatic filtering
    objects = TenantManager()
    # Keep default manager for admin/superuser access
    all_objects = models.Manager()

# In views:
from .managers import set_current_clinic

def my_view(request):
    # Set clinic context (usually done in middleware)
    set_current_clinic(request.user.clinic)

    # This will automatically filter by clinic
    patients = Patient.objects.all()

    # This bypasses the filter (admin only!)
    all_patients = Patient.all_objects.all()
"""
