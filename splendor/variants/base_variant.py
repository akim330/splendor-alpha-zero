# variants/base_variant.py
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Set
from ..components import Card, Noble

class SplendorVariant(ABC):
    """Base class for all Splendor game variants."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the game variant."""
        pass
    
    @property
    @abstractmethod
    def level_1_cards(self) -> Dict[int, Card]:
        """Level 1 cards for this variant."""
        pass
    
    @property
    @abstractmethod
    def level_2_cards(self) -> Dict[int, Card]:
        """Level 2 cards for this variant."""
        pass
    
    @property
    @abstractmethod
    def level_3_cards(self) -> Dict[int, Card]:
        """Level 3 cards for this variant."""
        pass
    
    @property
    @abstractmethod
    def nobles(self) -> List[Noble]:
        """Nobles for this variant."""
        pass
    
    @property
    def all_cards(self) -> Dict[int, Card]:
        """All cards in this variant."""
        return {**self.level_1_cards, **self.level_2_cards, **self.level_3_cards}
    
    @property
    def rows_per_level(self) -> int:
        """Number of card rows per level."""
        return 4
    
    @property
    def max_gems_per_color(self) -> int:
        """Maximum gems available for each color."""
        return 4
    
    @property
    def max_wild_gems(self) -> int:
        """Maximum wild/gold gems available."""
        return 5
    
    @property
    def max_reserved_cards(self) -> int:
        """Maximum cards a player can reserve."""
        return 3
    
    @property
    def target_score(self) -> int:
        """Score needed to trigger endgame."""
        return 15
    
    @property
    def noble_count(self) -> int:
        """Number of nobles to use in the game."""
        return 3