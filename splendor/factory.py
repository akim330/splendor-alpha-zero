# factory.py
from typing import Dict, Type
from .variants.base_variant import SplendorVariant
from .variants.standard_game import StandardSplendor
from .variants.simple_game import SimpleSplendor
from enum import Enum

class GameVariantFactory:
    """Factory for creating Splendor game variants."""
    
    # Registry of available game variants
    _variants: Dict[str, Type[SplendorVariant]] = {
        "standard": StandardSplendor,
        "simple": SimpleSplendor,
    }
    
    @classmethod
    def create_variant(cls, variant_name: str) -> SplendorVariant:
        """Create a specific game variant.
        
        Args:
            variant_name: Name of the variant to create
            
        Returns:
            Instance of the requested SplendorVariant
            
        Raises:
            ValueError: If the requested variant doesn't exist
        """
        variant_class = cls._variants.get(variant_name.lower())
        if not variant_class:
            available = ", ".join(cls._variants.keys())
            raise ValueError(f"Unknown variant '{variant_name}'. Available variants: {available}")
        
        return variant_class()
    
    @classmethod
    def register_variant(cls, name: str, variant_class: Type[SplendorVariant]) -> None:
        """Register a new game variant.
        
        Args:
            name: Name to register the variant under
            variant_class: Class implementing the variant
        """
        cls._variants[name.lower()] = variant_class