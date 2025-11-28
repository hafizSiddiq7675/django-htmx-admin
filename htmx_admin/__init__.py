"""
django-htmx-admin
HTMX-Powered Django Admin Enhancement

A drop-in enhancement package that adds HTMX-powered interactions to Django Admin.
"""

__version__ = '1.0.0'
__author__ = 'django-htmx-admin'
__license__ = 'MIT'

from .admin import HtmxModelAdmin
from .mixins import HtmxResponseMixin, HtmxFormMixin

__all__ = [
    'HtmxModelAdmin',
    'HtmxResponseMixin',
    'HtmxFormMixin',
]
