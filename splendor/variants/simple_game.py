import json
import os
from typing import Dict
from .base_variant import SplendorVariant
from ..components import Card, Noble
from ..configs.simple import level_1_cards, level_2_cards, level_3_cards, nobles_list

class SimpleSplendor(SplendorVariant):
    """Simple Splendor game with all rules and components."""
    
    def __init__(self):
        """Initialize simple Splendor game."""
        self._load_components()
    
    @property
    def name(self) -> str:
        return "Simple Splendor"
    
    @property
    def level_1_cards(self) -> Dict[int, Card]:
        return self._level_1_cards
    
    @property
    def level_2_cards(self) -> Dict[int, Card]:
        return self._level_2_cards
    
    @property
    def level_3_cards(self) -> Dict[int, Card]:
        return self._level_3_cards
    
    @property
    def nobles(self) -> list[Noble]:
        return self._nobles
    
    def _load_components(self):
        """Load cards and nobles from configuration file."""
        config_path = os.path.join(os.path.dirname(__file__), 
                                 '../configs/standard.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Load cards
        self._level_1_cards = {}
        self._level_2_cards = {}
        self._level_3_cards = {}
        
        # Load nobles
        self._nobles = nobles_list