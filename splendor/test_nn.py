import logging
import os

import coloredlogs

from Coach import Coach
from splendor.SplendorGame import SplendorGame as Game
from splendor.NNet import NNetWrapper as nn
from utils import *

from splendor.config import nobles_list

import numpy as np

verbose = False
output = "print"

debug_log_folder = "./logs"
next_index = "nn_test"
debug_file_path = f"{debug_log_folder}/{next_index}.txt"
display_time = False

g = Game(verbose=verbose, output=output, debug_file_path=debug_file_path, display_time=display_time)

nnet = nn(g, verbose=verbose, output=output, debug_file_path=debug_file_path)

def find_card(game, w, u, g, r, k):
    for c in game.cards:
        card = game.cards[c]
        if list(card.cost.values()) == [w, u, g, r, k]:
            return c
    return -1

def find_noble(w, u, g, r, k):
    for i, n in enumerate(nobles_list):
        if list(n.cost.values()) == [w, u, g, r, k]:
            return i
    return -1

board = [
    [3, 5, 3, 0, 3],
    [0, 0, 7, 0, 0],
    [0, 3, 6, 3, 0],
    [0, 0, 7, 3, 0],
    [0, 0, 5, 3, 0],
    [0, 0, 3, 2, 2],
    [0, 5, 3, 0, 0],
    [0, 0, 5, 0, 0],
    [1, 2, 1, 1, 0],
    [0, 0, 0, 0, 3],
    [0, 0, 0, 2, 1],
    [1, 1, 0, 1, 2]
]

nobles = [
    [4, 0, 0, 0, 4],
    [3, 3, 0, 0, 3],
    [0, 0, 3, 3, 3]
]

state = np.zeros(g.getBoardSize())

for card in board:
    i = find_card(g, card[0], card[1], card[2], card[3], card[4])
    state[i] = 1

for n in nobles:
    i = find_noble(n[0], n[1], n[2], n[3], n[4])
    state[(g.n_cards * 3 + 25) + i] = 1

# Current player
state[(g.n_cards * 3 + 24)] = 1

g.display_state_external(state, just_print=True)
