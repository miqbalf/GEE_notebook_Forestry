"""
Authentication module for Google Earth Engine integration.

This module provides utilities for initializing Google Earth Engine
with various authentication methods including service account credentials.
"""

from .main import initialize_gee, get_gee_credentials, check_gee_initialization, quick_init

__all__ = ['initialize_gee', 'get_gee_credentials', 'check_gee_initialization', 'quick_init']
