"""Catalog of review properties: agent definitions, claim type numbers and translations."""

from .catalog import PropertyCatalog
from .definition import AgentDefinition
from .errors import PropertyCatalogError
from .names import PropertyNames

__all__ = [
    "AgentDefinition",
    "PropertyCatalog",
    "PropertyCatalogError",
    "PropertyNames",
]
