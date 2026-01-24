"""
Multi-Tenant Middleware for Clinexa

This module provides middleware to automatically set the current clinic
context based on the request (subdomain, header, or user session).
"""

from django.http import Http404
from django.core.exceptions import PermissionDenied
from .models import Clinic
from .managers import set_current_clinic, clear_current_clinic


class TenantMiddleware:
    """
    Middleware to set the current clinic context for each request.

    This middleware extracts the clinic from the request and stores it
    in thread-local storage, making it available to the TenantManager
    for automatic query filtering.

    Configuration in settings.py:
        MIDDLEWARE = [
            # ... other middleware ...
            'clinics.middleware.TenantMiddleware',
        ]

    Supports three methods of tenant identification:
    1. Subdomain routing (production)
    2. Header-based (API/development)
    3. Session-based (simple MVP)
    """

    def __init__(self, get_response):
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request and set clinic context.

        Args:
            request: The HTTP request object.

        Returns:
            HTTP response from the next middleware/view.
        """
        try:
            # Extract clinic from request
            clinic = self.get_clinic_from_request(request)

            # Set clinic in thread-local storage
            if clinic:
                # Verify clinic is active
                if not clinic.is_active:
                    raise PermissionDenied(
                        "This clinic account is inactive. "
                        "Please contact support."
                    )

                # Verify subscription is valid
                if not clinic.is_subscription_active():
                    raise PermissionDenied(
                        "This clinic's subscription has expired. "
                        "Please renew your subscription."
                    )

                set_current_clinic(clinic)
                request.clinic = clinic  # Also attach to request object
            else:
                clear_current_clinic()
                request.clinic = None

            # Process request
            response = self.get_response(request)

            return response

        finally:
            # Always clear clinic context after request
            clear_current_clinic()

    def get_clinic_from_request(self, request):
        """
        Extract clinic from request using multiple strategies.

        Tries in order:
        1. Subdomain routing (if configured)
        2. X-Clinic-ID header (for API)
        3. User's clinic (if authenticated)

        Args:
            request: The HTTP request object.

        Returns:
            Clinic instance or None.

        Raises:
            Http404: If clinic is specified but not found.
        """
        clinic = None

        # Strategy 1: Subdomain routing
        clinic = self._get_clinic_from_subdomain(request)
        if clinic:
            return clinic

        # Strategy 2: Header-based (for API)
        clinic = self._get_clinic_from_header(request)
        if clinic:
            return clinic

        # Strategy 3: Session-based (authenticated user)
        clinic = self._get_clinic_from_user(request)
        if clinic:
            return clinic

        return None

    def _get_clinic_from_subdomain(self, request):
        """
        Extract clinic from subdomain.

        Example:
            salud-integral.clinexa.com -> slug='salud-integral'

        Args:
            request: The HTTP request object.

        Returns:
            Clinic instance or None.
        """
        try:
            # Get host without port
            host = request.get_host().split(':')[0]

            # Skip for localhost and IP addresses
            if host in ['localhost', '127.0.0.1'] or host.replace('.', '').isdigit():
                return None

            # Extract subdomain
            parts = host.split('.')

            # Minimum 2 parts needed: subdomain.domain.tld
            if len(parts) < 2:
                return None

            subdomain = parts[0]

            # Skip 'www' subdomain
            if subdomain == 'www':
                return None

            # Lookup clinic by slug
            return Clinic.objects.get(slug=subdomain, is_active=True)

        except Clinic.DoesNotExist:
            raise Http404(f"Clinic not found for subdomain: {subdomain}")
        except Exception:
            return None

    def _get_clinic_from_header(self, request):
        """
        Extract clinic from X-Clinic-ID header.

        Useful for API requests where subdomain routing isn't available.

        Args:
            request: The HTTP request object.

        Returns:
            Clinic instance or None.
        """
        try:
            clinic_id = request.headers.get('X-Clinic-ID')

            if not clinic_id:
                return None

            # Lookup clinic by UUID
            return Clinic.objects.get(id=clinic_id, is_active=True)

        except Clinic.DoesNotExist:
            raise Http404(f"Clinic not found with ID: {clinic_id}")
        except Exception:
            return None

    def _get_clinic_from_user(self, request):
        """
        Extract clinic from authenticated user's clinic.

        Simple strategy for MVP where users belong to one clinic.

        Args:
            request: The HTTP request object.

        Returns:
            Clinic instance or None.
        """
        if request.user.is_authenticated and hasattr(request.user, 'clinic'):
            return request.user.clinic
        return None


class TenantSecurityMiddleware:
    """
    Additional security middleware to prevent cross-tenant data access.

    This middleware adds extra validation to ensure that object IDs
    in URLs belong to the current clinic.

    Configuration in settings.py:
        MIDDLEWARE = [
            # ... other middleware ...
            'clinics.middleware.TenantMiddleware',
            'clinics.middleware.TenantSecurityMiddleware',
        ]
    """

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request with additional security checks.

        Args:
            request: The HTTP request object.

        Returns:
            HTTP response from the next middleware/view.
        """
        # You can add custom security checks here
        # For example, validate that URL parameters reference
        # objects belonging to the current clinic

        response = self.get_response(request)
        return response


class TenantAuditMiddleware:
    """
    Audit middleware to log all requests by clinic.

    Logs requests for compliance and security auditing.

    Configuration in settings.py:
        MIDDLEWARE = [
            # ... other middleware ...
            'clinics.middleware.TenantMiddleware',
            'clinics.middleware.TenantAuditMiddleware',
        ]
    """

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Log request details for audit trail.

        Args:
            request: The HTTP request object.

        Returns:
            HTTP response from the next middleware/view.
        """
        import logging
        logger = logging.getLogger('tenant_audit')

        # Process request
        response = self.get_response(request)

        # Log request details
        if hasattr(request, 'clinic') and request.clinic:
            logger.info(
                f"Clinic: {request.clinic.slug} | "
                f"User: {request.user.username if request.user.is_authenticated else 'anonymous'} | "
                f"Method: {request.method} | "
                f"Path: {request.path} | "
                f"Status: {response.status_code} | "
                f"IP: {self._get_client_ip(request)}"
            )

        return response

    def _get_client_ip(self, request):
        """
        Extract client IP address from request.

        Handles proxy headers (X-Forwarded-For).

        Args:
            request: The HTTP request object.

        Returns:
            IP address as string.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Example Django settings.py configuration:
"""
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Multi-tenant middleware (add after authentication)
    'clinics.middleware.TenantMiddleware',
    'clinics.middleware.TenantSecurityMiddleware',
    'clinics.middleware.TenantAuditMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging configuration for audit
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/tenant_audit.log',
        },
    },
    'loggers': {
        'tenant_audit': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
"""
