"""
FCD (Forest Canopy Density) Module

This module provides Forest Canopy Density calculation functionality.

Usage:
    # Import the main class directly from the package
    from osi.fcd import FCDCalc
    
    # Or import from the specific module
    from osi.fcd.main_fcd import FCDCalc
"""

from .main_fcd import FCDCalc

# Make FCDCalc available at package level
__all__ = ['FCDCalc']

