"""Portable research workflow core (Python 3.11+, standard library only)."""

# A single rolling edition is identified by its content fingerprints. Project
# schemas, record versions and bundle format versions remain separate contracts.
__version__ = "current"

from .model import (
    COLLECTIONS,
    RECORD_KINDS,
    SCHEMA_VERSION,
    export_schemas,
    validate_project,
    validate_record,
    validate_registry,
)

__all__ = [
    "COLLECTIONS",
    "RECORD_KINDS",
    "SCHEMA_VERSION",
    "export_schemas",
    "validate_project",
    "validate_record",
    "validate_registry",
]
