class Card():
    def __init__(self, level, color, pv, w, u, g, r, k):
        self.level = level
        self.color = color
        self.pv = pv
        self.cost = {
            'w': w,
            'u': u,
            'g': g,
            'r': r,
            'k': k
        }

    def __repr__(self):
        cost_strs = []
        for color in 'wugrk':
            if self.cost[color] != 0:
                cost_strs.append(f"{self.cost[color]}{color.upper()}")
        return f"Card(level={self.level}, color={self.color}, PV={self.pv}, {' ,'.join(cost_strs)})".ljust(50)


class Noble():
    def __init__(self, id, pv, w, u, g, r, k):
        self.id = id
        self.pv = pv

        self.cost = {
            'w': w,
            'u': u,
            'g': g,
            'r': r,
            'k': k
        }

    def __repr__(self):
        cost_strs = []
        for color in 'wugrk':
            if self.cost[color] != 0:
                cost_strs.append(f"{self.cost[color]}{color.upper()}")

        return f"Noble(id={self.id}, PV={self.pv}, {' ,'.join(cost_strs)})".ljust(30)


# level_1_cards_all = {
#     # LEVEL 1
#     0: Card(level=1, color="k", pv=0,
#             w=1, u=1, g=1, r=1, k=0),
#     1: Card(level=1, color="k", pv=0,
#             w=1, u=2, g=1, r=1, k=0),
#     2: Card(level=1, color="k", pv=0,
#             w=2, u=2, g=0, r=1, k=0),
#     3: Card(level=1, color="k", pv=0,
#             w=0, u=0, g=1, r=3, k=1),
#     4: Card(level=1, color="k", pv=0,
#             w=0, u=0, g=2, r=1, k=0),
#     5: Card(level=1, color="k", pv=0,
#             w=2, u=0, g=2, r=0, k=0),
#     6: Card(level=1, color="k", pv=0,
#             w=0, u=0, g=3, r=0, k=0),
#     7: Card(level=1, color="k", pv=1,
#             w=0, u=4, g=0, r=0, k=0),
#
#     8: Card(level=1, color="u", pv=0,
#             w=1, u=0, g=1, r=1, k=1),
#     9: Card(level=1, color="u", pv=0,
#             w=1, u=0, g=1, r=2, k=1),
#     10: Card(level=1, color="u", pv=0,
#              w=1, u=0, g=2, r=2, k=0),
#     11: Card(level=1, color="u", pv=0,
#              w=0, u=1, g=3, r=1, k=0),
#     12: Card(level=1, color="u", pv=0,
#              w=1, u=0, g=0, r=0, k=2),
#     13: Card(level=1, color="u", pv=0,
#              w=0, u=0, g=2, r=0, k=2),
#     14: Card(level=1, color="u", pv=0,
#              w=0, u=0, g=0, r=0, k=3),
#     15: Card(level=1, color="u", pv=1,
#              w=0, u=0, g=0, r=4, k=0),
#
#     16: Card(level=1, color="w", pv=0,
#              w=0, u=1, g=1, r=1, k=1),
#     17: Card(level=1, color="w", pv=0,
#              w=0, u=1, g=2, r=1, k=1),
#     18: Card(level=1, color="w", pv=0,
#              w=0, u=2, g=2, r=0, k=1),
#     19: Card(level=1, color="w", pv=0,
#              w=3, u=1, g=0, r=0, k=1),
#     20: Card(level=1, color="w", pv=0,
#              w=0, u=0, g=0, r=2, k=1),
#     21: Card(level=1, color="w", pv=0,
#              w=0, u=2, g=0, r=0, k=2),
#     22: Card(level=1, color="w", pv=0,
#              w=0, u=3, g=0, r=0, k=0),
#     23: Card(level=1, color="w", pv=1,
#              w=0, u=0, g=4, r=0, k=0),
#
#     24: Card(level=1, color="g", pv=0,
#              w=1, u=1, g=0, r=1, k=1),
#     25: Card(level=1, color="g", pv=0,
#              w=1, u=1, g=0, r=1, k=2),
#     26: Card(level=1, color="g", pv=0,
#              w=0, u=1, g=0, r=2, k=2),
#     27: Card(level=1, color="g", pv=0,
#              w=1, u=3, g=1, r=0, k=0),
#     28: Card(level=1, color="g", pv=0,
#              w=2, u=1, g=0, r=0, k=0),
#     29: Card(level=1, color="g", pv=0,
#              w=0, u=2, g=0, r=2, k=0),
#     30: Card(level=1, color="g", pv=0,
#              w=0, u=0, g=0, r=3, k=0),
#     31: Card(level=1, color="g", pv=1,
#              w=0, u=0, g=0, r=0, k=4),
#
#     32: Card(level=1, color="r", pv=0,
#              w=1, u=1, g=1, r=0, k=1),
#     33: Card(level=1, color="r", pv=0,
#              w=2, u=1, g=1, r=0, k=1),
#     34: Card(level=1, color="r", pv=0,
#              w=2, u=0, g=1, r=0, k=2),
#     35: Card(level=1, color="r", pv=0,
#              w=1, u=0, g=0, r=1, k=3),
#     36: Card(level=1, color="r", pv=0,
#              w=0, u=2, g=1, r=0, k=0),
#     37: Card(level=1, color="r", pv=0,
#              w=2, u=0, g=0, r=2, k=0),
#     38: Card(level=1, color="r", pv=0,
#              w=3, u=0, g=0, r=0, k=0),
#     39: Card(level=1, color="r", pv=1,
#              w=4, u=0, g=0, r=0, k=0),
# }

level_1_cards_all = {
    # LEVEL 1
    28: Card(level=1, color="g", pv=0,
             w=2, u=1, g=0, r=0, k=0),


    0: Card(level=1, color="k", pv=0,
            w=1, u=1, g=1, r=1, k=0),
    1: Card(level=1, color="k", pv=0,
            w=1, u=2, g=1, r=1, k=0),
    31: Card(level=1, color="g", pv=1,
             w=0, u=0, g=0, r=0, k=4),

    2: Card(level=1, color="k", pv=0,
            w=2, u=2, g=0, r=1, k=0),

    3: Card(level=1, color="k", pv=0,
            w=0, u=0, g=1, r=3, k=1),
    4: Card(level=1, color="k", pv=0,
            w=0, u=0, g=2, r=1, k=0),

    30: Card(level=1, color="g", pv=0,
             w=0, u=0, g=0, r=3, k=0),
    5: Card(level=1, color="k", pv=0,
            w=2, u=0, g=2, r=0, k=0),



    6: Card(level=1, color="k", pv=0,
            w=0, u=0, g=3, r=0, k=0),
    7: Card(level=1, color="k", pv=1,
            w=0, u=4, g=0, r=0, k=0),

    24: Card(level=1, color="g", pv=0,
             w=1, u=1, g=0, r=1, k=1),
    25: Card(level=1, color="g", pv=0,
             w=1, u=1, g=0, r=1, k=2),

    8: Card(level=1, color="u", pv=0,
            w=1, u=0, g=1, r=1, k=1),
    9: Card(level=1, color="u", pv=0,
            w=1, u=0, g=1, r=2, k=1),
    10: Card(level=1, color="u", pv=0,
             w=1, u=0, g=2, r=2, k=0),
    11: Card(level=1, color="u", pv=0,
             w=0, u=1, g=3, r=1, k=0),
    12: Card(level=1, color="u", pv=0,
             w=1, u=0, g=0, r=0, k=2),
    13: Card(level=1, color="u", pv=0,
             w=0, u=0, g=2, r=0, k=2),
    14: Card(level=1, color="u", pv=0,
             w=0, u=0, g=0, r=0, k=3),
    15: Card(level=1, color="u", pv=1,
             w=0, u=0, g=0, r=4, k=0),

    16: Card(level=1, color="w", pv=0,
             w=0, u=1, g=1, r=1, k=1),
    17: Card(level=1, color="w", pv=0,
             w=0, u=1, g=2, r=1, k=1),
    18: Card(level=1, color="w", pv=0,
             w=0, u=2, g=2, r=0, k=1),
    19: Card(level=1, color="w", pv=0,
             w=3, u=1, g=0, r=0, k=1),
    20: Card(level=1, color="w", pv=0,
             w=0, u=0, g=0, r=2, k=1),
    21: Card(level=1, color="w", pv=0,
             w=0, u=2, g=0, r=0, k=2),
    22: Card(level=1, color="w", pv=0,
             w=0, u=3, g=0, r=0, k=0),
    23: Card(level=1, color="w", pv=1,
             w=0, u=0, g=4, r=0, k=0),

    26: Card(level=1, color="g", pv=0,
             w=0, u=1, g=0, r=2, k=2),
    27: Card(level=1, color="g", pv=0,
             w=1, u=3, g=1, r=0, k=0),

    29: Card(level=1, color="g", pv=0,
             w=0, u=2, g=0, r=2, k=0),



    32: Card(level=1, color="r", pv=0,
             w=1, u=1, g=1, r=0, k=1),
    33: Card(level=1, color="r", pv=0,
             w=2, u=1, g=1, r=0, k=1),
    34: Card(level=1, color="r", pv=0,
             w=2, u=0, g=1, r=0, k=2),
    35: Card(level=1, color="r", pv=0,
             w=1, u=0, g=0, r=1, k=3),
    36: Card(level=1, color="r", pv=0,
             w=0, u=2, g=1, r=0, k=0),
    37: Card(level=1, color="r", pv=0,
             w=2, u=0, g=0, r=2, k=0),
    38: Card(level=1, color="r", pv=0,
             w=3, u=0, g=0, r=0, k=0),
    39: Card(level=1, color="r", pv=1,
             w=4, u=0, g=0, r=0, k=0),
}

level_1_cards = {}
for i, card in enumerate(list(level_1_cards_all.values())):
    level_1_cards[i] = card

n_level_1_cards = len(list(level_1_cards_all.values()))


level_2_cards_all = {
    # LEVEL 2
    # 40: Card(level=2, color="k", pv=1,
    #          w=3, u=2, g=2, r=0, k=0),
    63: Card(level=2, color="g", pv=3,
             w=0, u=0, g=6, r=0, k=0),
    62: Card(level=2, color="g", pv=2,
             w=0, u=0, g=5, r=0, k=0),
    41: Card(level=2, color="k", pv=1,
             w=3, u=0, g=3, r=0, k=2),
    42: Card(level=2, color="k", pv=2,
             w=0, u=1, g=4, r=2, k=0),
    43: Card(level=2, color="k", pv=2,
             w=0, u=0, g=5, r=3, k=0),
    # 44: Card(level=2, color="k", pv=2,
    #          w=5, u=0, g=0, r=0, k=0),
    # 45: Card(level=2, color="k", pv=3,
    #          w=0, u=0, g=0, r=0, k=6),
    #
    # 46: Card(level=2, color="u", pv=1,
    #          w=0, u=2, g=2, r=3, k=0),
    47: Card(level=2, color="u", pv=1,
             w=0, u=2, g=3, r=0, k=3),
    # 48: Card(level=2, color="u", pv=2,
    #          w=5, u=3, g=0, r=0, k=0),
    # 49: Card(level=2, color="u", pv=2,
    #          w=2, u=0, g=0, r=1, k=4),
    # 50: Card(level=2, color="u", pv=2,
    #          w=0, u=5, g=0, r=0, k=0),
    # 51: Card(level=2, color="u", pv=3,
    #          w=0, u=6, g=0, r=0, k=0),
    #
    52: Card(level=2, color="w", pv=1,
             w=0, u=0, g=3, r=2, k=2),
    # 53: Card(level=2, color="w", pv=1,
    #          w=2, u=3, g=0, r=3, k=0),
    # 54: Card(level=2, color="w", pv=2,
    #          w=0, u=0, g=1, r=4, k=2),
    # 55: Card(level=2, color="w", pv=2,
    #          w=0, u=0, g=0, r=5, k=3),
    # 56: Card(level=2, color="w", pv=2,
    #          w=0, u=0, g=0, r=5, k=0),
    # 57: Card(level=2, color="w", pv=3,
    #          w=6, u=0, g=0, r=0, k=0),

    # 58: Card(level=2, color="g", pv=1,
    #          w=3, u=0, g=2, r=3, k=0),
    # 59: Card(level=2, color="g", pv=1,
    #          w=2, u=3, g=0, r=0, k=2),
    # 60: Card(level=2, color="g", pv=2,
    #          w=4, u=2, g=0, r=0, k=1),
    61: Card(level=2, color="g", pv=2,
             w=0, u=5, g=3, r=0, k=0),



    # 64: Card(level=2, color="r", pv=1,
    #          w=2, u=0, g=0, r=2, k=3),
    # 65: Card(level=2, color="r", pv=1,
    #          w=0, u=3, g=0, r=2, k=3),
    # 66: Card(level=2, color="r", pv=2,
    #          w=1, u=4, g=2, r=0, k=0),
    # 67: Card(level=2, color="r", pv=2,
    #          w=3, u=0, g=0, r=0, k=5),
    # 68: Card(level=2, color="r", pv=2,
    #          w=0, u=0, g=0, r=0, k=5),
    # 69: Card(level=2, color="r", pv=3,
    #          w=0, u=0, g=0, r=6, k=0),
}

level_2_cards = {}
for i, card in enumerate(list(level_2_cards_all.values())):
    level_2_cards[i + n_level_1_cards] = card

n_level_2_cards = len(list(level_2_cards_all.values()))


level_3_cards_all = {
    # LEVEL 3

    # 70: Card(level=3, color="k", pv=3,
    #          w=3, u=3, g=5, r=3, k=0),
    # 71: Card(level=3, color="k", pv=4,
    #          w=0, u=0, g=0, r=7, k=0),
    # 72: Card(level=3, color="k", pv=4,
    #          w=0, u=0, g=3, r=6, k=3),
    # 73: Card(level=3, color="k", pv=5,
    #          w=0, u=0, g=0, r=7, k=3),
    #
    # 74: Card(level=3, color="u", pv=3,
    #          w=3, u=0, g=3, r=3, k=5),
    # 75: Card(level=3, color="u", pv=4,
    #          w=7, u=0, g=0, r=0, k=0),
    # 76: Card(level=3, color="u", pv=4,
    #          w=6, u=3, g=0, r=0, k=3),
    # 77: Card(level=3, color="u", pv=5,
    #          w=7, u=3, g=0, r=0, k=0),
    #
    # 78: Card(level=3, color="w", pv=3,
    #          w=0, u=3, g=3, r=5, k=3),
    # 79: Card(level=3, color="w", pv=4,
    #          w=0, u=0, g=0, r=0, k=7),
    # 80: Card(level=3, color="w", pv=4,
    #          w=3, u=0, g=0, r=3, k=6),
    # 81: Card(level=3, color="w", pv=5,
    #          w=3, u=0, g=0, r=0, k=7),
    #
    # 82: Card(level=3, color="g", pv=3,
    #          w=5, u=3, g=0, r=3, k=3),
    # 83: Card(level=3, color="g", pv=4,
    #          w=0, u=7, g=0, r=0, k=0),
    # 84: Card(level=3, color="g", pv=4,
    #          w=3, u=6, g=3, r=0, k=0),
    # 85: Card(level=3, color="g", pv=5,
    #          w=0, u=7, g=3, r=0, k=0),

    86: Card(level=3, color="r", pv=3,
             w=3, u=5, g=3, r=0, k=3),
    87: Card(level=3, color="r", pv=4,
             w=0, u=0, g=7, r=0, k=0),
    88: Card(level=3, color="r", pv=4,
             w=0, u=3, g=6, r=3, k=0),
    89: Card(level=3, color="r", pv=5,
             w=0, u=0, g=7, r=3, k=0)
}

level_3_cards = {}
for i, card in enumerate(list(level_3_cards_all.values())):
    level_3_cards[i + n_level_1_cards + n_level_2_cards] = card

n_level_3_cards = len(list(level_3_cards_all.values()))



nobles_list = [
    Noble(id=0, pv=3,
          w=0, u=0, g=4, r=4, k=0),
    Noble(id=1, pv=3,
          w=3, u=0, g=0, r=3, k=3),
    Noble(id=2, pv=3,
          w=4, u=4, g=0, r=0, k=0),
    Noble(id=3, pv=3,
          w=4, u=0, g=0, r=0, k=4),
    Noble(id=4, pv=3,
          w=0, u=4, g=4, r=0, k=0),
    Noble(id=5, pv=3,
          w=0, u=3, g=3, r=3, k=0),
    Noble(id=6, pv=3,
          w=3, u=3, g=3, r=0, k=0),
    Noble(id=7, pv=3,
          w=0, u=0, g=0, r=4, k=4),
    Noble(id=8, pv=3,
          w=3, u=3, g=0, r=0, k=3),
    Noble(id=9, pv=3,
          w=0, u=0, g=3, r=3, k=3),
]