from abc import ABC
from enum import Enum
from typing import Dict, List


class Card():
    def __init__(self, level : int, color : str, pv : int, w : int, u : int, g : int, r : int, k : int):
        self.level : int = level
        self.color : str = color
        self.pv : int = pv
        self.cost : Dict[str, int] = {
            'w': w,
            'u': u,
            'g': g,
            'r': r,
            'k': k
        }

    def __repr__(self):
        cost_strs : List[str] = []
        for color in 'wugrk':
            if self.cost[color] != 0:
                cost_strs.append(f"{self.cost[color]}{color.upper()}")
        return f"Card(level={self.level}, color={self.color}, PV={self.pv}, {' ,'.join(cost_strs)})".ljust(50)


class Noble():
    def __init__(self, id : int, pv : int, w : int, u : int, g : int, r : int, k : int):
        self.id : int = id
        self.pv : int = pv

        self.cost = {
            'w': w,
            'u': u,
            'g': g,
            'r': r,
            'k': k
        }

    def __repr__(self):
        cost_strs : List[str] = []
        for color in 'wugrk':
            if self.cost[color] != 0:
                cost_strs.append(f"{self.cost[color]}{color.upper()}")

        return f"Noble(id={self.id}, PV={self.pv}, {' ,'.join(cost_strs)})".ljust(30)

class SplendorGameVariant(Enum):
    LEVEL_0_2G1U = "level_0_2g1u"
    LEVEL_0_4U = "level_0_4u"
    LEVEL_1_GRK = "level_1_grk"
    VANILLA = "vanilla"

# Abstract configuration class
class SplendorConfig(ABC):
    """Base configuration class for different variants of the game"""
    _registry : Dict[SplendorGameVariant, 'SplendorConfig'] = {}

    def __init__(
        self, 
        variant: SplendorGameVariant,
        row_1_cards: Dict[int, Card],
        row_2_cards: Dict[int, Card],
        row_3_cards: Dict[int, Card],
        nobles: List[Noble],
        target_score: int
    ):
        self.variant : SplendorGameVariant = variant
        self.level_1_cards : Dict[int, Card] = row_1_cards
        self.level_2_cards : Dict[int, Card] = row_2_cards
        self.level_3_cards : Dict[int, Card] = row_3_cards
        self.cards : Dict[int, Card] = {**row_1_cards, **row_2_cards, **row_3_cards}
        self.nobles : List[Noble] = nobles
        self.target_score : int = target_score

        self.n_level_1_cards : int = len(row_1_cards)
        self.n_level_2_cards : int = len(row_2_cards)
        self.n_level_3_cards : int = len(row_3_cards)
        self.n_cards : int = len(row_1_cards) + len(row_2_cards) + len(row_3_cards)
        self.n_nobles : int = len(nobles)

        self._registry[variant] = self

    @classmethod
    def get_config(cls, variant: SplendorGameVariant):
        return cls._registry[variant]

LEVEL_0_2G1U = SplendorConfig(
    variant=SplendorGameVariant.LEVEL_0_2G1U,
    row_1_cards= {
        0: Card(level=1, color="k", pv=1, w=0, u=0, g=2, r=1, k=0),
        1: Card(level=1, color="k", pv=0, w=2, u=0, g=2, r=0, k=0),
        2: Card(level=1, color="k", pv=0, w=0, u=0, g=3, r=0, k=0),
        3: Card(level=1, color="k", pv=0, w=0, u=4, g=0, r=0, k=0),
    },
    row_2_cards = {
        4: Card(level=2, color="k", pv=3, w=0, u=0, g=0, r=0, k=6),
        5: Card(level=2, color="u", pv=1, w=0, u=2, g=3, r=0, k=3),
        6: Card(level=2, color="u", pv=2, w=2, u=0, g=0, r=1, k=4),
        7: Card(level=2, color="r", pv=2, w=0, u=0, g=0, r=0, k=5),
        8: Card(level=2, color="r", pv=2, w=0, u=0, g=0, r=0, k=5),
    },
    row_3_cards = {
        9: Card(level=3, color="u", pv=3, w=3, u=0, g=3, r=3, k=5),
        10: Card(level=3, color="w", pv=4, w=0, u=0, g=0, r=0, k=7),
        11: Card(level=3, color="w", pv=4, w=3, u=0, g=0, r=3, k=6),
        12: Card(level=3, color="w", pv=5, w=3, u=0, g=0, r=0, k=7),
    },
    nobles = list({
        0: Noble(id=0, pv=3, w=4, u=0, g=0, r=0, k=4),
        1: Noble(id=1, pv=3, w=0, u=0, g=0, r=4, k=4),
        2: Noble(id=2, pv=3, w=0, u=0, g=3, r=3, k=3),
    }.values()),
    target_score=1
)

LEVEL_0_4U = SplendorConfig(
    variant=SplendorGameVariant.LEVEL_0_4U,
    row_1_cards= {
        0: Card(level=1, color="k", pv=0, w=0, u=0, g=2, r=1, k=0),
        1: Card(level=1, color="k", pv=0, w=2, u=0, g=2, r=0, k=0),
        2: Card(level=1, color="k", pv=0, w=0, u=0, g=3, r=0, k=0),
        3: Card(level=1, color="k", pv=1, w=0, u=4, g=0, r=0, k=0),
    },
    row_2_cards = {
        4: Card(level=2, color="k", pv=3, w=0, u=0, g=0, r=0, k=6),
        5: Card(level=2, color="u", pv=1, w=0, u=2, g=3, r=0, k=3),
        6: Card(level=2, color="u", pv=2, w=2, u=0, g=0, r=1, k=4),
        7: Card(level=2, color="r", pv=2, w=3, u=0, g=0, r=0, k=5),
        8: Card(level=2, color="r", pv=2, w=0, u=0, g=0, r=0, k=5),
    },
    row_3_cards = {
        9: Card(level=3, color="u", pv=3, w=3, u=0, g=3, r=3, k=5),
        10: Card(level=3, color="w", pv=4, w=0, u=0, g=0, r=0, k=7),
        11: Card(level=3, color="w", pv=4, w=3, u=0, g=0, r=3, k=6),
        12: Card(level=3, color="w", pv=5, w=3, u=0, g=0, r=0, k=7),
    },
    nobles = list({
        0: Noble(id=0, pv=3, w=4, u=0, g=0, r=0, k=4),
        1: Noble(id=1, pv=3, w=0, u=0, g=0, r=4, k=4),
        2: Noble(id=2, pv=3, w=0, u=0, g=3, r=3, k=3),
    }.values()),
    target_score=1
)

LEVEL_1_GRK = SplendorConfig(
    variant=SplendorGameVariant.LEVEL_1_GRK,
    row_1_cards = {
        0: Card(level=1, color="w", pv=0, w=0, u=0, g=1, r=2, k=1),
        1: Card(level=1, color="u", pv=0, w=1, u=0, g=2, r=1, k=0),
        2: Card(level=1, color="g", pv=0, w=2, u=1, g=0, r=0, k=1),
        3: Card(level=1, color="r", pv=0, w=0, u=2, g=1, r=0, k=1),
        4: Card(level=1, color="k", pv=0, w=1, u=1, g=1, r=1, k=0),
        5: Card(level=1, color="w", pv=1, w=0, u=0, g=3, r=0, k=1),
        6: Card(level=1, color="u", pv=1, w=0, u=0, g=0, r=3, k=1),
        7: Card(level=1, color="g", pv=1, w=2, u=0, g=0, r=0, k=2),
        8: Card(level=1, color="r", pv=1, w=3, u=1, g=0, r=0, k=0),
        9: Card(level=1, color="k", pv=1, w=0, u=3, g=1, r=0, k=0),
    },
    row_2_cards = {
        10: Card(level=2, color="w", pv=2, w=0, u=0, g=3, r=2, k=2),
        11: Card(level=2, color="u", pv=2, w=0, u=2, g=3, r=0, k=3),
        12: Card(level=2, color="g", pv=2, w=4, u=2, g=0, r=0, k=1),
        13: Card(level=2, color="r", pv=2, w=0, u=0, g=5, r=0, k=0),
        14: Card(level=2, color="k", pv=2, w=0, u=5, g=0, r=0, k=0),
    },
    row_3_cards = {
        15: Card(level=3, color="k", pv=3, w=3, u=0, g=3, r=3, k=2),
        16: Card(level=3, color="w", pv=3, w=0, u=3, g=3, r=5, k=0),
        17: Card(level=3, color="r", pv=4, w=0, u=0, g=7, r=0, k=0),
        18: Card(level=3, color="w", pv=5, w=3, u=0, g=0, r=0, k=7),
    },
    nobles = list({
        0: Noble(id=0, pv=3, w=4, u=0, g=0, r=0, k=4),
        1: Noble(id=1, pv=3, w=0, u=0, g=0, r=4, k=4),
        2: Noble(id=2, pv=3, w=0, u=0, g=3, r=3, k=3),
    }.values()),
    target_score=2
)

VANILLA = SplendorConfig(
    variant=SplendorGameVariant.VANILLA,
        row_1_cards = {
        0: Card(level=1, color="k", pv=0, w=1, u=1, g=1, r=1, k=0),
        1: Card(level=1, color="k", pv=0, w=1, u=2, g=1, r=1, k=0),
        2: Card(level=1, color="k", pv=0, w=2, u=2, g=0, r=1, k=0),
        3: Card(level=1, color="k", pv=0, w=0, u=0, g=1, r=3, k=1),
        4: Card(level=1, color="k", pv=0, w=0, u=0, g=2, r=1, k=0),
        5: Card(level=1, color="k", pv=0, w=2, u=0, g=2, r=0, k=0),
        6: Card(level=1, color="k", pv=0, w=0, u=0, g=3, r=0, k=0),
        7: Card(level=1, color="k", pv=1, w=0, u=4, g=0, r=0, k=0),

        8: Card(level=1, color="u", pv=0, w=1, u=0, g=1, r=1, k=1),
        9: Card(level=1, color="u", pv=0, w=1, u=0, g=1, r=2, k=1),
        10: Card(level=1, color="u", pv=0, w=1, u=0, g=2, r=2, k=0),
        11: Card(level=1, color="u", pv=0, w=0, u=1, g=3, r=1, k=0),
        12: Card(level=1, color="u", pv=0, w=1, u=0, g=0, r=0, k=2),
        13: Card(level=1, color="u", pv=0, w=0, u=0, g=2, r=0, k=2),
        14: Card(level=1, color="u", pv=0, w=0, u=0, g=0, r=0, k=3),
        15: Card(level=1, color="u", pv=1, w=0, u=0, g=0, r=4, k=0),

        16: Card(level=1, color="w", pv=0, w=0, u=1, g=1, r=1, k=1),
        17: Card(level=1, color="w", pv=0, w=0, u=1, g=2, r=1, k=1),
        18: Card(level=1, color="w", pv=0, w=0, u=2, g=2, r=0, k=1),
        19: Card(level=1, color="w", pv=0, w=3, u=1, g=0, r=0, k=1),
        20: Card(level=1, color="w", pv=0, w=0, u=0, g=0, r=2, k=1),
        21: Card(level=1, color="w", pv=0, w=0, u=2, g=0, r=0, k=2),
        22: Card(level=1, color="w", pv=0, w=0, u=3, g=0, r=0, k=0),
        23: Card(level=1, color="w", pv=1, w=0, u=0, g=4, r=0, k=0),

        24: Card(level=1, color="g", pv=0, w=1, u=1, g=0, r=1, k=1),
        25: Card(level=1, color="g", pv=0, w=1, u=1, g=0, r=1, k=2),
        26: Card(level=1, color="g", pv=0, w=0, u=1, g=0, r=2, k=2),
        27: Card(level=1, color="g", pv=0, w=1, u=3, g=1, r=0, k=0),
        28: Card(level=1, color="g", pv=0, w=2, u=1, g=0, r=0, k=0),
        29: Card(level=1, color="g", pv=0, w=0, u=0, g=0, r=3, k=0),
        30: Card(level=1, color="g", pv=0, w=0, u=2, g=0, r=2, k=0),
        31: Card(level=1, color="g", pv=1, w=0, u=0, g=0, r=0, k=4),

        32: Card(level=1, color="r", pv=0, w=1, u=1, g=1, r=0, k=1),
        33: Card(level=1, color="r", pv=0, w=2, u=1, g=1, r=0, k=1),
        34: Card(level=1, color="r", pv=0, w=2, u=0, g=1, r=0, k=2),
        35: Card(level=1, color="r", pv=0, w=1, u=0, g=0, r=1, k=3),
        36: Card(level=1, color="r", pv=0, w=0, u=2, g=1, r=0, k=0),
        37: Card(level=1, color="r", pv=0, w=2, u=0, g=0, r=2, k=0),
        38: Card(level=1, color="r", pv=0, w=3, u=0, g=0, r=0, k=0),
        39: Card(level=1, color="r", pv=1, w=4, u=0, g=0, r=0, k=0),
    },
    row_2_cards = {
        40: Card(level=2, color="k", pv=1,
                w=3, u=2, g=2, r=0, k=0),
        41: Card(level=2, color="k", pv=1,
                w=3, u=0, g=3, r=0, k=2),
        42: Card(level=2, color="k", pv=2,
                w=0, u=1, g=4, r=2, k=0),
        43: Card(level=2, color="k", pv=2,
                w=0, u=0, g=5, r=3, k=0),
        44: Card(level=2, color="k", pv=2,
                w=5, u=0, g=0, r=0, k=0),
        45: Card(level=2, color="k", pv=3,
                w=0, u=0, g=0, r=0, k=6),
        
        46: Card(level=2, color="u", pv=1,
                w=0, u=2, g=2, r=3, k=0),
        47: Card(level=2, color="u", pv=1,
                w=0, u=2, g=3, r=0, k=3),
        48: Card(level=2, color="u", pv=2,
                w=5, u=3, g=0, r=0, k=0),
        49: Card(level=2, color="u", pv=2,
                w=2, u=0, g=0, r=1, k=4),
        50: Card(level=2, color="u", pv=2,
                w=0, u=5, g=0, r=0, k=0),
        51: Card(level=2, color="u", pv=3,
                w=0, u=6, g=0, r=0, k=0),
        
        52: Card(level=2, color="w", pv=1,
                w=0, u=0, g=3, r=2, k=2),
        53: Card(level=2, color="w", pv=1,
                w=2, u=3, g=0, r=3, k=0),
        54: Card(level=2, color="w", pv=2,
                w=0, u=0, g=1, r=4, k=2),
        55: Card(level=2, color="w", pv=2,
                w=0, u=0, g=0, r=5, k=3),
        56: Card(level=2, color="w", pv=2,
                w=0, u=0, g=0, r=5, k=0),
        57: Card(level=2, color="w", pv=3,
                w=6, u=0, g=0, r=0, k=0),

        58: Card(level=2, color="g", pv=1,
                w=3, u=0, g=2, r=3, k=0),
        59: Card(level=2, color="g", pv=1,
                w=2, u=3, g=0, r=0, k=2),
        60: Card(level=2, color="g", pv=2,
                w=4, u=2, g=0, r=0, k=1),
        61: Card(level=2, color="g", pv=2,
                w=0, u=5, g=3, r=0, k=0),
        62: Card(level=2, color="g", pv=2,
                w=0, u=0, g=5, r=0, k=0),
        63: Card(level=2, color="g", pv=3,
                w=0, u=0, g=6, r=0, k=0),

        64: Card(level=2, color="r", pv=1,
                w=2, u=0, g=0, r=2, k=3),
        65: Card(level=2, color="r", pv=1,
                w=0, u=3, g=0, r=2, k=3),
        66: Card(level=2, color="r", pv=2,
                w=1, u=4, g=2, r=0, k=0),
        67: Card(level=2, color="r", pv=2,
                w=3, u=0, g=0, r=0, k=5),
        68: Card(level=2, color="r", pv=2,
                w=0, u=0, g=0, r=0, k=5),
        69: Card(level=2, color="r", pv=3,
                w=0, u=0, g=0, r=6, k=0),
    },
    row_3_cards = {
        70: Card(level=3, color="k", pv=3,
                w=3, u=3, g=5, r=3, k=0),
        71: Card(level=3, color="k", pv=4,
                w=0, u=0, g=0, r=7, k=0),
        72: Card(level=3, color="k", pv=4,
                w=0, u=0, g=3, r=6, k=3),
        73: Card(level=3, color="k", pv=5,
                w=0, u=0, g=0, r=7, k=3),
        
        74: Card(level=3, color="u", pv=3,
                w=3, u=0, g=3, r=3, k=5),
        75: Card(level=3, color="u", pv=4,
                w=7, u=0, g=0, r=0, k=0),
        76: Card(level=3, color="u", pv=4,
                w=6, u=3, g=0, r=0, k=3),
        77: Card(level=3, color="u", pv=5,
                w=7, u=3, g=0, r=0, k=0),
        
        78: Card(level=3, color="w", pv=3,
                w=0, u=3, g=3, r=5, k=3),
        79: Card(level=3, color="w", pv=4,
                w=0, u=0, g=0, r=0, k=7),
        80: Card(level=3, color="w", pv=4,
                w=3, u=0, g=0, r=3, k=6),
        81: Card(level=3, color="w", pv=5,
                w=3, u=0, g=0, r=0, k=7),
        
        82: Card(level=3, color="g", pv=3,
                w=5, u=3, g=0, r=3, k=3),
        83: Card(level=3, color="g", pv=4,
                w=0, u=7, g=0, r=0, k=0),
        84: Card(level=3, color="g", pv=4,
                w=3, u=6, g=3, r=0, k=0),
        85: Card(level=3, color="g", pv=5,
                w=0, u=7, g=3, r=0, k=0),

        86: Card(level=3, color="r", pv=3,
                w=3, u=5, g=3, r=0, k=3),
        87: Card(level=3, color="r", pv=4,
                w=0, u=0, g=7, r=0, k=0),
        88: Card(level=3, color="r", pv=4,
                w=0, u=3, g=6, r=3, k=0),
        89: Card(level=3, color="r", pv=5,
                w=0, u=0, g=7, r=3, k=0)
    },
    nobles = list({
        0: Noble(id=0, pv=3,
            w=0, u=0, g=4, r=4, k=0),
        1: Noble(id=1, pv=3,
            w=3, u=0, g=0, r=3, k=3),
        2: Noble(id=2, pv=3,
            w=4, u=4, g=0, r=0, k=0),
        3: Noble(id=3, pv=3,
            w=4, u=0, g=0, r=0, k=4),
        4: Noble(id=4, pv=3,
            w=0, u=4, g=4, r=0, k=0),
        5: Noble(id=5, pv=3,
            w=0, u=3, g=3, r=3, k=0),
        6: Noble(id=6, pv=3,
            w=3, u=3, g=3, r=0, k=0),
        7: Noble(id=7, pv=3,
            w=0, u=0, g=0, r=4, k=4),
        8: Noble(id=8, pv=3,
            w=3, u=3, g=0, r=0, k=3),
        9: Noble(id=9, pv=3,
            w=0, u=0, g=3, r=3, k=3),
    }.values()),
    target_score=15
)

