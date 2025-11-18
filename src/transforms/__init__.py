"""
Transform Modules for Automated Pivoting

This package contains modular transforms that take input selectors
and discover related intelligence through automated pivoting.

Architecture:
- BaseTransform: Abstract class defining transform interface
- Specific transforms: EmailTransform, UsernameTransform, etc.
- PivotEngine: Orchestrates automated transform execution

Each transform follows the pattern:
    Input Selector → API/Database Query → Output Entities + Metadata
"""

from .base_transform import BaseTransform, TransformResult, Selector

__all__ = ['BaseTransform', 'TransformResult', 'Selector']
