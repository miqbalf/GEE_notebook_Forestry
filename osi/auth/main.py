"""
Google Earth Engine Authentication Module

This module provides functions for initializing Google Earth Engine
with service account credentials and other authentication methods.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import ee
from google.oauth2 import service_account


def initialize_gee(credentials_path: Optional[str] = None, 
                   project_id: Optional[str] = None,
                   use_service_account: bool = True) -> bool:
    """
    Initialize Google Earth Engine with service account credentials.
    
    Args:
        credentials_path (str, optional): Path to the service account JSON file.
                                         Defaults to '/usr/src/app/user_id.json' in container
                                         or './gcp_credentials.json' locally.
        project_id (str, optional): Google Cloud Project ID. If not provided,
                                   will be read from credentials file.
        use_service_account (bool): Whether to use service account authentication.
                                   If False, will use user authentication.
    
    Returns:
        bool: True if initialization successful, False otherwise.
    
    Example:
        >>> # Using service account
        >>> success = initialize_gee()
        >>> 
        >>> # Using custom credentials path
        >>> success = initialize_gee(credentials_path='./my_credentials.json')
        >>> 
        >>> # Using user authentication
        >>> success = initialize_gee(use_service_account=False)
    """
    try:
        if use_service_account:
            return _initialize_with_service_account(credentials_path, project_id)
        else:
            return _initialize_with_user_auth(project_id)
            
    except Exception as e:
        print(f"✗ Error initializing GEE: {e}")
        return False


def _initialize_with_service_account(credentials_path: Optional[str] = None, 
                                   project_id: Optional[str] = None) -> bool:
    """Initialize GEE using service account credentials."""
    try:
        # Determine credentials path
        if credentials_path is None:
            # Try container path first, then local path
            container_path = '/usr/src/app/user_id.json'
            local_path = './gcp_credentials.json'
            
            if os.path.exists(container_path):
                credentials_path = container_path
            elif os.path.exists(local_path):
                credentials_path = local_path
            else:
                print(f"✗ No credentials file found. Tried:")
                print(f"  - {container_path}")
                print(f"  - {local_path}")
                return False
        
        # Load credentials from file
        with open(credentials_path, 'r') as f:
            credentials_data = json.load(f)
        
        service_account_email = credentials_data.get('client_email')
        if not service_account_email:
            print("✗ No 'client_email' found in credentials file")
            return False
        
        # Get project ID
        if project_id is None:
            project_id = credentials_data.get('project_id')
            if not project_id:
                print("✗ No 'project_id' found in credentials file")
                return False
        
        # Initialize Earth Engine with service account
        credentials = ee.ServiceAccountCredentials(service_account_email, credentials_path)
        ee.Initialize(credentials, project=project_id)
        
        print(f"✓ GEE Initialized successfully")
        # print(f"  Service Account: {service_account_email}")
        # print(f"  Project ID: {project_id}")
        print(f"  Credentials Path: {credentials_path} - loaded successfully")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ Credentials file not found: {credentials_path}")
        return False
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in credentials file: {credentials_path}")
        return False
    except Exception as e:
        print(f"✗ Error with service account authentication: {e}")
        return False


def _initialize_with_user_auth(project_id: Optional[str] = None) -> bool:
    """Initialize GEE using user authentication."""
    try:
        # Authenticate user (this will open a browser)
        ee.Authenticate()
        
        # Initialize with project
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
        
        print(f"✓ GEE Initialized successfully with user authentication")
        if project_id:
            # print(f"  Project ID: {project_id}")
            None
        
        return True
        
    except Exception as e:
        print(f"✗ Error with user authentication: {e}")
        return False


def get_gee_credentials(credentials_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load and return GEE credentials from a JSON file.
    
    Args:
        credentials_path (str, optional): Path to the credentials file.
                                         Defaults to standard paths.
    
    Returns:
        dict: Credentials data if successful, None otherwise.
    
    Example:
        >>> creds = get_gee_credentials()
        >>> if creds:
        ...     print(f"Project: {creds['project_id']}")
        ...     print(f"Service Account: {creds['client_email']}")
    """
    try:
        # Determine credentials path
        if credentials_path is None:
            container_path = '/usr/src/app/user_id.json'
            local_path = './gcp_credentials.json'
            
            if os.path.exists(container_path):
                credentials_path = container_path
            elif os.path.exists(local_path):
                credentials_path = local_path
            else:
                print(f"✗ No credentials file found")
                return None
        
        # Load credentials
        with open(credentials_path, 'r') as f:
            credentials_data = json.load(f)
        
        # Validate required fields
        required_fields = ['client_email', 'project_id', 'private_key']
        missing_fields = [field for field in required_fields if field not in credentials_data]
        
        if missing_fields:
            print(f"✗ Missing required fields in credentials: {missing_fields}")
            return None
        
        return credentials_data
        
    except FileNotFoundError:
        print(f"✗ Credentials file not found: {credentials_path}")
        return None
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON in credentials file: {credentials_path}")
        return None
    except Exception as e:
        print(f"✗ Error loading credentials: {e}")
        return None


def check_gee_initialization() -> bool:
    """
    Check if Google Earth Engine is properly initialized.
    
    Returns:
        bool: True if GEE is initialized, False otherwise.
    
    Example:
        >>> if check_gee_initialization():
        ...     print("GEE is ready to use!")
        ... else:
        ...     print("GEE needs to be initialized")
    """
    try:
        # Try to get a simple image to test initialization
        test_image = ee.Image('COPERNICUS/S2_SR/20210101T100319_20210101T100321_T32UPA')
        test_image.getInfo()
        return True
    except Exception:
        return False


# Convenience function for quick initialization
def quick_init(project_id: str) -> bool:
    """
    Quick initialization of GEE with default settings.
    
    Args:
        project_id (str): Google Cloud Project ID
    
    Returns:
        bool: True if successful, False otherwise.
    
    Example:
        >>> if quick_init():
        ...     print("Ready to use GEE!")
    """
    return initialize_gee(project_id=project_id)
