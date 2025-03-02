from __future__ import print_function

import copy
import sys
from typing import Dict, List

sys.path.append('..')
# from Game import Game
import numpy as np
from numpy.typing import NDArray

import random
# import queue
from collections import deque

import re

import time

from splendor.config import SplendorConfig, SplendorGameVariant

import os


take_coins_actions = ['wug', 'wur', 'wuk', 'wgr', 'wgk', 'wrk', 'ugr', 'ugk', 'urk', 'grk', 'wu', 'wg', 'wr', 'wk', 'ug',
                      'ur', 'uk', 'gr', 'gk', 'rk', 'w', 'u', 'g', 'r', 'k', 'ww', 'uu', 'gg', 'rr', 'kk', '']

cards_per_row_count = 4

randomize_branch = False

class SplendorGameState():
    def __init__(self, id_decks : Dict[int, deque[int]], board : NDArray[np.int_], reserved : Dict[int, NDArray[np.int_]], nobles_board : NDArray[np.int_], coins : Dict[int, Dict[str, int]], perma_gems : Dict[int, Dict[str, int]], scores : Dict[int, int], gained_nobles : Dict[int, List[int]],
                 consecutive_do_nothings : int):
        self.id_decks : Dict[int, deque[int]] = id_decks
        self.board : NDArray[np.int_] = board
        self.reserved : Dict[int, NDArray[np.int_]] = reserved
        self.nobles_board : NDArray[np.int_] = nobles_board
        self.coins : Dict[int, Dict[str, int]] = coins
        self.perma_gems : Dict[int, Dict[str, int]] = perma_gems
        self.scores : Dict[int, int] = scores
        self.gained_nobles : Dict[int, List[int]] = gained_nobles
        self.consecutive_do_nothings : int = consecutive_do_nothings


class SplendorGame():
    # @staticmethod
    # def getSquarePiece(piece):
    #     return SplendorGame.square_content[piece]

    def __init__(
        self, 
        game_variant : SplendorGameVariant = SplendorGameVariant.VANILLA, 
        verbose : bool = False, 
        output : str = "print", 
        debug_file_path : str | None = None, 
        display_time : bool = False, 
        randomize : bool = True
    ):
        self.verbose : bool = verbose
        self.config : SplendorConfig = SplendorConfig.get_config(game_variant)

        self.states = {}
        self.output : str = output
        self.debug_file_path : str | None = debug_file_path

        self.randomize : bool = randomize

        self.current_valid_moves = []

        self.display_time : bool = display_time

        self.n_actions : int = self.config.n_cards * 2 + 33 + 1

        self.take_coins_action_dict : Dict[int, str] = {}
        for i in range(31):
            self.take_coins_action_dict[self.config.n_cards * 2 + i + 3] = take_coins_actions[i]


        self.color_str_to_action_dict : Dict[str, int] = {}
        for action in self.take_coins_action_dict:
            self.color_str_to_action_dict[self.take_coins_action_dict[action]] = action


        self.times : Dict[str, float] = {}
        self.reset_times()

        self.reset_main()


    def reset_times(self):
        self.times = {
            'reset': 0,
            'next': 0,
            'valid': 0,
            'reset_randomize': 0,
            'reset_misc': 0,
            'reset_branch': 0,
            'string_representation': 0,
            'string_representation0': 0,
            'string_representation1': 0,
            'string_representation2': 0,
            'display_game_state': 0,
            'get_canonical_form': 0
        }

    def log(self, s : str, print_to_terminal : bool = False):
        if self.verbose:
            if self.output == 'file':
                if self.debug_file_path is None:
                    raise ValueError("debug_file_path is None but output is 'file'")
                with open(self.debug_file_path, 'a') as f:
                    f.write(f"{s}\n")
            if print_to_terminal:   
                print(s)

            elif self.output == 'print':
                print(s)

    def reset_main(self):
        self.reset_times()

        start_time = time.time()

        id_list1 = list(range(self.config.n_level_1_cards))
        id_list2 = list(range(self.config.n_level_1_cards, self.config.n_level_1_cards + self.config.n_level_2_cards))
        id_list3 = list(range(self.config.n_level_1_cards + self.config.n_level_2_cards, self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards))

        if self.randomize:
            random.shuffle(id_list1)
            random.shuffle(id_list2)
            random.shuffle(id_list3)

        time1 = time.time()

        deck1 = deque(id_list1)
        deck2 = deque(id_list2)
        deck3 = deque(id_list3)

        # for card in id_list1:
        #     deck1.put(card)
        # for card in id_list2:
        #     deck2.put(card)
        # for card in id_list3:
        #     deck3.put(card)

        id_decks = {
            1: deck1,
            2: deck2,
            3: deck3
        }

        board = np.zeros(self.config.n_cards, dtype=int)
        reserved = {
            1: np.zeros(self.config.n_cards, dtype = int),
            2: np.zeros(self.config.n_cards, dtype = int)
        }

        # Draw 4 cards for each level
        for _ in range(cards_per_row_count):
            current_card_id = id_decks[1].popleft()
            board[current_card_id] = 1

            current_card_id = id_decks[2].popleft()
            board[current_card_id] = 1

            current_card_id = id_decks[3].popleft()
            board[current_card_id] = 1

        # Pick 3 nobles
        n_nobles = len(self.config.nobles)
        nobles_board = np.zeros(n_nobles, dtype=int)
        n_to_sample = np.min([3, n_nobles])
        if self.randomize:
            nobles_board[random.sample(range(n_nobles), n_to_sample)] = 1
        else:
            nobles_board[[0, 1, 2]] = 1

        # Player coins
        coins = {
            1: {
                'w': 0,
                'u': 0,
                'g': 0,
                'r': 0,
                'k': 0,
                'y': 0
            },
            2: {
                'w': 0,
                'u': 0,
                'g': 0,
                'r': 0,
                'k': 0,
                'y': 0
            }
        }

        # Player coins
        perma_gems = {
            1: {
                'w': 0,
                'u': 0,
                'g': 0,
                'r': 0,
                'k': 0,
            },
            2: {
                'w': 0,
                'u': 0,
                'g': 0,
                'r': 0,
                'k': 0,
            }
        }

        # Scores
        scores = {
            1: 0,
            2: 0
        }

        gained_nobles : Dict[int, List[int]] = {
            1: [],
            2: []
        }

        consecutive_do_nothings = 0

        game_state = SplendorGameState(id_decks, board, reserved, nobles_board, coins, perma_gems, scores,
                                       gained_nobles, consecutive_do_nothings)
        self.states = {
            'main': game_state,
            'branch': None
        }

        time2 = time.time()

        self.times['reset'] += time2 - start_time
        self.times['reset_randomize'] += time1 - start_time
        self.times['reset_misc'] += time2 - time1


    def getInitBoard(self):
        # return initial board (numpy board)
        return None

    def reset_branch(self):
        start_time = time.time()

        # Shuffle queues
        id_decks = {}

        for level in [1, 2, 3]:
            l = list(self.states['main'].id_decks[level])
            if self.randomize:
                random.shuffle(l)
            id_decks[level] = deque(l)

            # temp_storage = []
            # while not self.states['main'].id_decks[level].empty():
            #     el = self.states['main'].id_decks[level].get()
            #     l.append(el)
            #     temp_storage.append(el)
            # for item in temp_storage:
            #     self.states['main'].id_decks[level].put(item)
            #
            # random.shuffle(l)
            # for item in l:
            #     id_decks[level].put(item)

        time1 = time.time()

        self.states['branch'] = SplendorGameState(
            id_decks,
            self.states['main'].board.copy(),
            copy.deepcopy(self.states['main'].reserved),
            self.states['main'].nobles_board.copy(),
            copy.deepcopy(self.states['main'].coins),
            copy.deepcopy(self.states['main'].perma_gems),
            copy.deepcopy(self.states['main'].scores),
            copy.deepcopy(self.states['main'].gained_nobles),
            self.states['main'].consecutive_do_nothings
        )

        self.times['reset_branch'] += time1 - start_time


    def getBoardSize(self):
        # 90 cards on board or not
        # 90 cards reserved by player or not
        # 90 cards reserved by opponent or not
        # 10 card values (5 for player and 5 for opponent)
        # 12 coin values (6 for player and 6 for opponent)
        # 2 scores (for player + opponent)
        # 1 indicator for whether player went first
        # 10 nobles
        return self.config.n_cards * 3 + 10 + 12 + 2 + 1 + self.config.n_nobles

    def checkBoard(self, m_or_b):
        pass
        # assert np.sum(self.states[m_or_b].board[:40]) <= 4, f"Have too many Level 1 cards: {self.states[m_or_b].board}"
        # assert np.sum(
        #     self.states[m_or_b].board[40:70]) <= 4, f"Have too many Level 2 cards: {self.states[m_or_b].board}"
        # assert np.sum(
        #     self.states[m_or_b].board[70:90]) <= 4, f"Have too many Level 3 cards: {self.states[m_or_b].board}"
        #
        # assert np.sum(self.states[m_or_b].reserved[
        #                   1] == 1) < 4, f"Player 1 has too many reserved cards: {self.states[m_or_b].reserved}"
        # assert np.sum(self.states[m_or_b].reserved[
        #                   2] == 1) < 4, f"Player 2 has too many reserved cards: {self.states[m_or_b].reserved}"

    def getActionSize(self):
        # 214 TOTAL
        # 90 cards to buy
        # 90 cards to reserve
        # 3 random pile cards to reserve
        # 10 (5 choose 3) ways to take 3 coins
        # 10 (5 choose 2) ways to take 2 coins
        # 5 (5 choose 1) ways to take 1 coin
        # 5 ways to take 2 of the same color
        # 1 way to do nothing

        # 0 - 89 --> Buy card of same ID
        # 90 - 179 --> Reserve card of n - 90 ID
        # 180 --> Reserve level 1 card
        # 181 --> Reserve level 2 card
        # 182 --> Reserve level 3 card
        # Take 3 coins
        # 183 --> WUG
        # 184 --> WUR
        # 185 --> WUK
        # 186 --> WGR
        # 187 --> WGK
        # 188 --> WRK
        # 189 --> UGR
        # 190 --> UGK
        # 191 --> URK
        # 192 --> GRK
        # Take 2 coins
        # 193 --> WU
        # 194 --> WG
        # 195 --> WR
        # 196 --> WK
        # 197 --> UG
        # 198 --> UR
        # 199 --> UK
        # 200 --> GR
        # 201 --> GK
        # 202 --> RK
        # Take 1 coin:
        # 203 --> W
        # 204 --> U
        # 205 --> G
        # 206 --> R
        # 207 --> K
        # 208 --> 2 Ws
        # 209 --> 2 Us
        # 210 --> 2 Gs
        # 211 --> 2 Rs
        # 212 --> 2 Ks
        # 213 --> no coins

        return self.config.n_cards * 2 + 3 + 10 + 10 + 5 + 5 + 1

    def card_id_to_level(self, id):
        if 0 <= id <= self.config.n_level_1_cards:
            return 1
        elif self.config.n_level_1_cards <= id <= self.config.n_level_1_cards + self.config.n_level_2_cards:
            return 2
        elif self.config.n_level_1_cards + self.config.n_level_2_cards <= id <= self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards:
            return 3
        else:
            raise Exception(f"id {id} isn't a valid card")

    def switch_player(self, player):
        return 3 - player

    def replenish_board(self, level, m_or_b):
        if len(self.states[m_or_b].id_decks[level]) == 0:
            self.log(f"Tried to draw card from level {level} but it's empty!")
            return
        else:
            new_id = self.states[m_or_b].id_decks[level].popleft()
            self.states[m_or_b].board[new_id] = 1

    def getNextState(self, board, player, action, m_or_b, print_to_terminal = False):
        start_time = time.time()

        # if player takes action on board, return next (board,player)
        # action must be a valid move

        # print(f"DEBUG: getting next state for {m_or_b}")

        action_str = "" # For logging

        if action < 0:
            raise Exception("Action can't be negative")
        elif action < self.config.n_cards:
            # Buy the card
            id_to_buy = action
            if self.states[m_or_b].board[id_to_buy] == 1:
                # Remove card from board
                self.states[m_or_b].board[id_to_buy] = 0

                # Draw new card to take its place
                level = self.card_id_to_level(id_to_buy)
                self.replenish_board(level, m_or_b)


            elif self.states[m_or_b].reserved[player][id_to_buy] == 1:
                # Remove card from reserved
                self.states[m_or_b].reserved[player][id_to_buy] = 0

            else:
                raise Exception(f"""
                    Player {player} taking action {action} trying to buy card {id_to_buy} but neither available to buy nor reserved by that player
                        Board: {self.states[m_or_b].board}
                        Reserved: {self.states[m_or_b].reserved}
                    """)

            # Take away player's coins
            card = self.config.cards[id_to_buy]
            before_coins = self.states[m_or_b].coins[player].copy()
            for color in card.cost:
                coins_needed = np.max([card.cost[color] - self.states[m_or_b].perma_gems[player][color], 0])
                if self.states[m_or_b].coins[player][color] >= coins_needed:
                    self.states[m_or_b].coins[player][color] -= coins_needed
                else:
                    self.states[m_or_b].coins[player]['y'] -= coins_needed - self.states[m_or_b].coins[player][color]

                    self.states[m_or_b].coins[player][color] = 0
                assert self.states[m_or_b].coins[player][color] >= 0 and self.states[m_or_b].coins[player][
                    'y'] >= 0, f"""Negative coin values for player {player} after buying: {self.states[m_or_b].coins[player]}"""

            # Add card to player gem count
            before_gems = self.states[m_or_b].perma_gems.copy()
            self.states[m_or_b].perma_gems[player][card.color] += 1

            # Add point value to player's score
            before_score = self.states[m_or_b].scores[player]
            self.states[m_or_b].scores[player] += card.pv

            # Check for nobles

            best_noble_i = -1
            best_opponent_distance_score = np.inf

            for idx in np.where(self.states[m_or_b].nobles_board == 1)[0]:
                noble = self.config.nobles[idx]
                qualified = True

                for color in noble.cost:
                    if self.states[m_or_b].perma_gems[player][color] < noble.cost[color]:
                        qualified = False
                        break

                if qualified:
                    # Determine best noble to get
                    opponent_distance_score = 0

                    for color in noble.cost:
                        if self.states[m_or_b].perma_gems[self.switch_player(player)][color] < noble.cost[color]:
                            opponent_distance_score += noble.cost[color] - \
                                                       self.states[m_or_b].perma_gems[self.switch_player(player)][color]

                    if opponent_distance_score < best_opponent_distance_score:
                        best_noble_i = idx
                        best_opponent_distance_score = opponent_distance_score

            if best_noble_i != -1:
                # Noble acquired
                self.states[m_or_b].scores[player] += self.config.nobles[best_noble_i].pv

                self.states[m_or_b].gained_nobles[player].append(self.config.nobles[best_noble_i])

                noble_s = f"""Acquired noble: {self.config.nobles[best_noble_i]}"""

                # Delete noble from the list
                self.states[m_or_b].nobles_board[best_noble_i] = 0

            else:
                noble_s = ""

            action_str = f"""Player {player} bought card {id_to_buy}: {self.config.cards[id_to_buy]}"""


        elif action < self.config.n_cards * 2:
            # Reserve card
            id_to_reserve = action - self.config.n_cards

            if self.states[m_or_b].board[id_to_reserve] == 1:
                # Remove card from board
                self.states[m_or_b].board[id_to_reserve] = 0

                # Draw new card to take its place
                level = self.card_id_to_level(id_to_reserve)
                self.replenish_board(level, m_or_b)

            else:
                raise Exception(f"""
                    Player {player} taking action {action} trying to reserve card {id_to_reserve} but not on the board
                        Board: {self.states[m_or_b].board}
                    """)

            # Add card to player reserved
            before_reserved = self.states[m_or_b].reserved.copy()
            self.states[m_or_b].reserved[player][id_to_reserve] = 1

            # Add yellow coin if possible
            before_coins = self.states[m_or_b].coins[player]['y']

            if self.states[m_or_b].coins[player]['y'] + self.states[m_or_b].coins[self.switch_player(player)]['y'] < 5:
                self.states[m_or_b].coins[player]['y'] += 1
                if sum(self.states[m_or_b].coins[player].values()) > 10:
                    # Throw away a random color
                    random_color = 'wugrk'[np.random.choice(
                        np.where(np.array(list(self.states[m_or_b].coins[player].values()))[:5] > 0)[0])]
                    self.states[m_or_b].coins[player][random_color] -= 1

            action_str = f"""Player {player} reserved card {id_to_reserve}: {self.config.cards[id_to_reserve]}"""


        elif self.config.n_cards * 2 <= action <= self.config.n_cards * 2 + 2:
            # 180 --> Reserve level 1 card
            # 181 --> Reserve level 2 card
            # 182 --> Reserve level 3 card
            level = action - (self.config.n_cards * 2) + 1
            # Draw card from the appropriate deck
            new_id = self.states[m_or_b].id_decks[level].popleft()
            self.states[m_or_b].reserved[player][new_id] = 1

            # Add yellow card if possible
            before_coins = self.states[m_or_b].coins[player]['y']
            if self.states[m_or_b].coins[player]['y'] + self.states[m_or_b].coins[self.switch_player(player)]['y'] < 5:
                self.states[m_or_b].coins[player]['y'] += 1

            action_str = f"""Player {player} reserved card from level {level}: {self.config.cards[new_id]}"""


        elif self.config.n_cards * 2 + 3 <= action <= self.config.n_cards * 2 + 32:
            # Take coins
            coins_string = self.take_coins_action_dict[action]
            before_coins = self.states[m_or_b].coins[player].copy()
            for color in coins_string:
                # Check if can't take color
                assert self.states[m_or_b].coins[player][color] + self.states[m_or_b].coins[self.switch_player(player)][
                    color] < 4, f"Can't take color {color}. Player 1 has {self.states[m_or_b].coins[1][color]}. Player 2 has {self.states[m_or_b].coins[2][color]}"
                self.states[m_or_b].coins[player][color] += 1

            action_str = f"""Player {player} took coins: {coins_string}"""

        elif action == self.config.n_cards * 2 + 33:
            # Do nothing
            # print("##### DID NOTHING 1 #######")
            action_str = f"""Player {player} did nothing"""
            pass
        else:
            raise Exception(f"Unrecognized action: {action}")

        if action == self.config.n_cards * 2 + 33:
            # print("##### DID NOTHING 2 #######")
            self.states[m_or_b].consecutive_do_nothings += 1
        else:
            self.states[m_or_b].consecutive_do_nothings = 0

        self.checkBoard(m_or_b)
        # print(f"Player returned: {self.switch_player(player)}")

        self.times['next'] += time.time() - start_time

        self.log("\t" + action_str, print_to_terminal = print_to_terminal and self.verbose)

        return None, self.switch_player(player)

        #
        # if action == self.n*self.n:
        #     return (board, -player)
        # b = Board(self.n)
        # b.pieces = np.copy(board)
        # move = (int(action/self.n), action%self.n)
        # b.execute_move(move, player)
        # return (b.pieces, -player)

    def can_buy(self, buying_power, yellow_possessed, card_cost):
        yellow_needed = 0
        for color in card_cost:
            if card_cost[color] > buying_power[color]:
                yellow_needed += card_cost[color] - buying_power[color]
        return yellow_possessed >= yellow_needed

    def set_current_valid_moves(self, player, m_or_b):
        self.current_valid_moves = self.getValidMoves(None, player, m_or_b)

    def getValidMoves(self, board, player, m_or_b):
        start_time = time.time()

        start_i = self.config.n_cards * 2

        s = self.stringRepresentation(player, m_or_b)

        valid_moves = np.zeros(self.getActionSize(), dtype=int)

        buying_power = {}

        for color in 'wugrk':
            buying_power[color] = self.states[m_or_b].perma_gems[player][color] + self.states[m_or_b].coins[player][
                color]

        # 209 TOTAL
        # 0-89 cards to buy
        for i in range(self.config.n_cards):
            if (self.states[m_or_b].board[i] or self.states[m_or_b].reserved[player][i]) and self.can_buy(buying_power,
                                                                                                          self.states[
                                                                                                              m_or_b].coins[
                                                                                                              player][
                                                                                                              'y'],
                                                                                                          self.config.cards[
                                                                                                              i].cost):
                valid_moves[i] = 1

        # 90 - 179 cards to reserve
        if np.sum(self.states[m_or_b].reserved[player] == 1) < 3:
            valid_moves[self.config.n_cards:self.config.n_cards * 2] = self.states[m_or_b].board
            # print(f"BOARD {m_or_b}: {self.states[m_or_b].board}")
            # print(f"Debug 2: {valid_moves}")
            # self.display_game_state(m_or_b)
            # 180, 181, 182: 3 random pile cards to reserve
            if not len(self.states[m_or_b].id_decks[1]) == 0:
                valid_moves[self.config.n_cards  * 2] = 1
            if not len(self.states[m_or_b].id_decks[2]) == 0:
                valid_moves[self.config.n_cards  * 2 + 1] = 1
            if not len(self.states[m_or_b].id_decks[3]) == 0:
                valid_moves[self.config.n_cards  * 2 + 2] = 1

        n_player_coins = np.sum(list(self.states[m_or_b].coins[player].values()))
        coins_left = {}

        for color in 'wugrk':
            coins_left[color] = 4 - self.states[m_or_b].coins[1][color] - self.states[m_or_b].coins[2][color]

        # 213 --> no coins
        if n_player_coins == 10:
            valid_moves[self.config.n_cards  * 2 + 33] = 1

        # 203 --> W
        # 204 --> U
        # 205 --> G
        # 206 --> R
        # 207 --> K
        elif n_player_coins == 9:
            for i, color in enumerate('wugrk'):
                if coins_left[color] > 0:
                    valid_moves[self.config.n_cards * 2 + 23 + i] = 1


        elif n_player_coins == 8:
            for i, color in enumerate('wugrk'):
                if coins_left[color] == 4:
                    # 208 --> 2 Ws
                    # 209 --> 2 Us
                    # 210 --> 2 Gs
                    # 211 --> 2 Rs
                    # 212 --> 2 Ks
                    valid_moves[self.config.n_cards * 2 + 28 + i] = 1

            # 193 --> WU
            # 194 --> WG
            # 195 --> WR
            # 196 --> WK
            # 197 --> UG
            # 198 --> UR
            # 199 --> UK
            # 200 --> GR
            # 201 --> GK
            # 202 --> RK
            valid_moves[start_i + 13] = coins_left['w'] > 0 and coins_left['u'] > 0
            valid_moves[start_i + 14] = coins_left['w'] > 0 and coins_left['g'] > 0
            valid_moves[start_i + 15] = coins_left['w'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 16] = coins_left['w'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 17] = coins_left['u'] > 0 and coins_left['g'] > 0
            valid_moves[start_i + 18] = coins_left['u'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 19] = coins_left['u'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 20] = coins_left['g'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 21] = coins_left['g'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 22] = coins_left['r'] > 0 and coins_left['k'] > 0

            coins_left_arr = np.array(list(coins_left.values()))
            nonzero_is = np.where(coins_left_arr > 0)[0]
            if len(nonzero_is) == 1:
                # only one color left
                valid_moves[start_i + 23 + nonzero_is] = 1


        elif n_player_coins <= 7:
            # 183 --> WUG
            # 184 --> WUR
            # 185 --> WUK
            # 186 --> WGR
            # 187 --> WGK
            # 188 --> WRK
            # 189 --> UGR
            # 190 --> UGK
            # 191 --> URK
            # 192 --> GRK
            valid_moves[start_i + 3] = coins_left['w'] > 0 and coins_left['u'] > 0 and coins_left['g'] > 0
            valid_moves[start_i + 4] = coins_left['w'] > 0 and coins_left['u'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 5] = coins_left['w'] > 0 and coins_left['u'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 6] = coins_left['w'] > 0 and coins_left['g'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 7] = coins_left['w'] > 0 and coins_left['g'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 8] = coins_left['w'] > 0 and coins_left['r'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 9] = coins_left['u'] > 0 and coins_left['g'] > 0 and coins_left['r'] > 0
            valid_moves[start_i + 10] = coins_left['u'] > 0 and coins_left['g'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 11] = coins_left['u'] > 0 and coins_left['r'] > 0 and coins_left['k'] > 0
            valid_moves[start_i + 12] = coins_left['g'] > 0 and coins_left['r'] > 0 and coins_left['k'] > 0

            coins_left_arr = np.array(list(coins_left.values()))
            # Only 1 color left
            if np.sum(coins_left_arr > 0) == 1:
                valid_moves[start_i + 23 + np.where(coins_left_arr > 0)[0][0]] = 1

            # Only 2 colors left
            if np.sum(coins_left_arr > 0) == 2:
                colors = "".join(np.array(list(coins_left.keys()))[np.where(coins_left_arr > 0)[0]])

                if colors == 'wu':
                    idx = start_i + 13
                elif colors == 'wg':
                    idx = start_i + 14
                elif colors == 'wr':
                    idx = start_i + 15
                elif colors == 'wk':
                    idx = start_i + 16
                elif colors == 'ug':
                    idx = start_i + 17
                elif colors == 'ur':
                    idx = start_i + 18
                elif colors == 'uk':
                    idx = start_i + 19
                elif colors == 'gr':
                    idx = start_i + 20
                elif colors == 'gk':
                    idx = start_i + 21
                elif colors == 'rk':
                    idx = start_i + 22
                else:
                    raise Exception(f"Invalid 2-color string: {colors}")

                valid_moves[idx] = 1

            for i, color in enumerate('wugrk'):
                if coins_left[color] == 4:
                    # 208 --> 2 Ws
                    # 209 --> 2 Us
                    # 210 --> 2 Gs
                    # 211 --> 2 Rs
                    # 212 --> 2 Ks
                    valid_moves[start_i + 28 + i] = 1
        # print(f"DEBUG 3: {valid_moves}")
        self.times['valid'] += time.time() - start_time

        return valid_moves

    def dict_values_sum(self, dict):
        return np.sum(np.array(list(dict.values())))

    def getGameEnded(self, board, player, m_or_b, print_to_terminal = False):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost

        # print(f"#### ARE THERE CONSECUTIVE DO NOTHINGS? {self.states[m_or_b].consecutive_do_nothings}")
        if self.states[m_or_b].consecutive_do_nothings >= 2:
            self.log("Game ended on consecutive do nothings!", print_to_terminal = print_to_terminal and self.verbose)
            return -2

        if np.sum(self.current_valid_moves) == 0: # type: ignore
            self.log(f"Game ended on no valid moves!", print_to_terminal = print_to_terminal and self.verbose)
            return -1

        if player == 2:
            return 0
        if player == 1:  # Can only end if just ended player 2's turn (assuming player 1 went first)
            winningConditionMet : bool = self.states[m_or_b].scores[1] >= self.config.target_score or self.states[m_or_b].scores[2] >= self.config.target_score
            opponent : int = self.switch_player(player)
            if winningConditionMet:
                log_string = f"Game ended. Player 1: {self.states[m_or_b].scores[1]} pts, player 2: {self.states[m_or_b].scores[2]} pts, target: {self.config.target_score} pts => "

                if self.states[m_or_b].scores[1] == self.states[m_or_b].scores[2]:
                    player_gems = self.dict_values_sum(self.states[m_or_b].perma_gems[player])
                    opponent_gems = self.dict_values_sum(self.states[m_or_b].perma_gems[opponent])
                    if player_gems > opponent_gems:
                        self.log(log_string + f"Tied but player {player} has more permanent gems! -> Player {opponent} wins", print_to_terminal = print_to_terminal and self.verbose)
                        return -1
                    elif player_gems < opponent_gems:
                        self.log(log_string + f"Tied but player {opponent} has more permanent gems! -> Player {player} wins", print_to_terminal = print_to_terminal and self.verbose)
                        return 1
                    else:
                        self.log(log_string + "Tied and both players have the same number of permanent gems! -> Draw", print_to_terminal = print_to_terminal and self.verbose)
                        return -2
                elif self.states[m_or_b].scores[player] > self.states[m_or_b].scores[opponent]:
                    self.log(log_string + f"Player {player} wins", print_to_terminal = print_to_terminal and self.verbose)
                    return 1
                elif self.states[m_or_b].scores[player] < self.states[m_or_b].scores[opponent]:
                    self.log(log_string + f"Player {opponent} wins", print_to_terminal = print_to_terminal and self.verbose)
                    return -1
                else:
                    raise Exception(f"""
                    Something went wrong with end-of-game score comparison
                        Scores: {self.states[m_or_b].scores}
                        
                        Perma-gems: {self.states[m_or_b].perma_gems}
                    """)
            else:
                self.log(f"Game not over yet since scores are {self.states[m_or_b].scores} and target score is {self.config.target_score}")
                return 0

    def getCanonicalForm(self, board, player, m_or_b):
        # return state from the point of view of player

        # 90 cards on board or not
        # 90 cards reserved by player or not
        # 90 cards reserved by opponent or not
        # 10 card values (5 for player and 5 for opponent)
        # 12 coin values (6 for player and 6 for opponent)
        # 2 scores (for player + opponent)
        # 1 indicator for whether player went first
        # 10 nobles

        start_time = time.time()
        if player == 1:
            arr =  np.concatenate(
                [self.states[m_or_b].board, self.states[m_or_b].reserved[1], self.states[m_or_b].reserved[2],
                 list(self.states[m_or_b].perma_gems[1].values()), list(self.states[m_or_b].perma_gems[2].values()),
                 list(self.states[m_or_b].coins[1].values()), list(self.states[m_or_b].coins[2].values()),
                 [self.states[m_or_b].scores[1], self.states[m_or_b].scores[2], 1],
                 self.states[m_or_b].nobles_board
                 ], dtype=int)
        elif player == 2:
            arr = np.concatenate(
                [self.states[m_or_b].board, self.states[m_or_b].reserved[2], self.states[m_or_b].reserved[1],
                 list(self.states[m_or_b].perma_gems[2].values()), list(self.states[m_or_b].perma_gems[1].values()),
                 list(self.states[m_or_b].coins[2].values()), list(self.states[m_or_b].coins[1].values()),
                 [self.states[m_or_b].scores[2], self.states[m_or_b].scores[1], -1],
                 self.states[m_or_b].nobles_board
                 ], dtype=int)

        else:
            raise Exception(f"Invalid player {player}")
        self.times['get_canonical_form'] += time.time() - start_time

        return arr

    def getSymmetries(self, board, pi):
        # mirror, rotational
        # assert(len(pi) == self.n**2+1)  # 1 for pass
        # pi_board = np.reshape(pi[:-1], (self.n, self.n))
        # l = []
        #
        # for i in range(1, 5):
        #     for j in [True, False]:
        #         newB = np.rot90(board, i)
        #         newPi = np.rot90(pi_board, i)
        #         if j:
        #             newB = np.fliplr(newB)
        #             newPi = np.fliplr(newPi)
        #         l += [(newB, list(newPi.ravel()) + [pi[-1]])]
        # return l

        return [(board, pi)]

    def stringRepresentation(self, player, m_or_b):
        # print(f"Stringy: {player}, {m_or_b}")
        start_time = time.time()
        canonical_form = self.getCanonicalForm(None, player, m_or_b)
        time1 = time.time()

        # 292: player 1 score
        # 293: player 2 score
        canonical_form[self.config.n_cards * 3 + 22] = str(canonical_form[self.config.n_cards * 3 + 22]).zfill(2)
        canonical_form[self.config.n_cards * 3 + 23] = str(canonical_form[self.config.n_cards * 3 + 23]).zfill(2)
        time2 = time.time()
        # print(f"Stringy canon: {canonical_form}")
        #arr =  ''.join(map(str, canonical_form))
        #arr = str(canonical_form)
        arr = canonical_form.tobytes()
        # if self.verbose:
        #     print(f"canonicalForm: {canonical_form}\nbytes: {arr}")
        time3 = time.time()
        self.times['string_representation'] += time.time() - start_time

        self.times['string_representation0'] += time1 - start_time
        self.times['string_representation1'] += time2 - time1
        self.times['string_representation2'] += time3 - time2


        return arr

    # def stringRepresentationReadable(self, board):
    #     board_s = "".join(self.square_content[square] for row in board for square in row)
    #     return board_s

    def getScore(self, player, m_or_b):
        return self.states[m_or_b].scores[player]

    def beautify_board(self, m_or_b):
        level_1_cards = []
        level_2_cards = []
        level_3_cards = []

        for i in np.where(self.states[m_or_b].board == 1)[0]:
            if i < self.config.n_level_1_cards:
                level_1_cards.append(self.config.cards[i])
            elif i < self.config.n_level_1_cards + self.config.n_level_2_cards:
                level_2_cards.append(self.config.cards[i])
            elif i < self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards:
                level_3_cards.append(self.config.cards[i])
            else:
                raise Exception(f"Invalid card i {i}")

        return f"""
        Level 3: {' | '.join([str(card) for card in level_3_cards])}
        Level 2: {' | '.join([str(card) for card in level_2_cards])}
        Level 1: {' | '.join([str(card) for card in level_1_cards])}"""

    def beautify_perma_gems(self, m_or_b):
        s = ""
        for player in [1, 2]:
            s += f"""
            Player {player}:
            """
            for color in 'wugrk':
                s += f""" {color.upper()}: {self.states[m_or_b].perma_gems[player][color]} """
        return s

    def beautify_coins(self, m_or_b):
        s = ""
        for player in [1, 2]:
            s += f"""
            Player {player}:
            """
            for color in 'wugrk':
                if self.states[m_or_b].perma_gems[player][color] > 0:
                    perma_gem_str = f"[{self.states[m_or_b].perma_gems[player][color]}]"
                else:
                    perma_gem_str = ""
                s += f""" {color.upper()}: {perma_gem_str}{self.states[m_or_b].coins[player][color]} """
            s += f""" Y: {self.states[m_or_b].coins[player]['y']} """

        return s

    def beautify_coins_left(self, m_or_b):
        color_strs = []
        for color in 'wugrk':
            coins_left = 4 - self.states[m_or_b].coins[1][color] - self.states[m_or_b].coins[2][color]
            color_strs.append(f"{coins_left}{color}")

        color_strs.append(f"{5 - self.states[m_or_b].coins[1]['y'] - self.states[m_or_b].coins[2]['y']}y")

        return ' '.join(color_strs)
        # for player in [1,2]:
        #     s += f"""
        #     Player {player}:
        #     """
        #     for color in 'wugrk':
        #         if self.perma_gems[player][color] > 0:
        #             perma_gem_str = f"[{self.perma_gems[player][color]}]"
        #         else:
        #             perma_gem_str = ""
        #         s += f""" {color.upper()}: {perma_gem_str}{self.coins[player][color]} """
        #     s += f""" Y: {self.coins[player]['y']} """
        #
        # return s

    def beautify_reserved(self, m_or_b):
        p1_cards = []
        p2_cards = []

        for i in np.where(self.states[m_or_b].reserved[1] == 1)[0]:
            p1_cards.append(self.config.cards[i])
        for i in np.where(self.states[m_or_b].reserved[2] == 1)[0]:
            p2_cards.append(self.config.cards[i])

        return f"""
        Player 1: {' | '.join([str(card) for card in p1_cards])}
        Player 2: {' | '.join([str(card) for card in p2_cards])}"""

    def beautify_nobles(self, m_or_b):
        return f"""
        Available: {' | '.join([str(noble) for noble in np.array(self.config.nobles)[np.array(self.states[m_or_b].nobles_board).astype(bool)]])}
        Player 1: {' | '.join([str(noble) for noble in self.states[m_or_b].gained_nobles[1]])}
        Player 2: {' | '.join([str(noble) for noble in self.states[m_or_b].gained_nobles[2]])}"""

    def convert_action_to_readable(self, a):
        if a < self.config.n_cards:
            return f"Buy {self.config.cards[a]}"
        elif a < self.config.n_cards * 2:
            return f"Reserve {self.config.cards[a - self.config.n_cards]}"
        elif a == self.config.n_cards * 2:
            return "Reserve random 1"
        elif a == self.config.n_cards * 2 + 1:
            return "Reserve random 2"
        elif a == self.config.n_cards * 2 + 2:
            return "Reserve random 3"
        else:
            if a not in self.take_coins_action_dict:
                raise Exception(f"Invalid action {a} in dict {self.take_coins_action_dict}")
            return self.take_coins_action_dict[a]

    def display_state_external(self, state, just_print = False):
        level_1_cards = []
        level_2_cards = []
        level_3_cards = []

        tabs = '\t\t'



        # Board
        for i in np.where(state[:self.config.n_cards] == 1)[0]:
            if i < self.config.n_level_1_cards:
                level_1_cards.append(self.config.cards[i])
            elif i < self.config.n_level_1_cards + self.config.n_level_2_cards:
                level_2_cards.append(self.config.cards[i])
            elif i < self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards:
                level_3_cards.append(self.config.cards[i])
            else:
                raise Exception(f"Invalid card i {i}")

        # Coins left
        color_strs = []
        coins_1 = state[(self.config.n_cards * 3 + 10):(self.config.n_cards * 3 + 16)]
        coins_2 = state[(self.config.n_cards * 3 + 16):(self.config.n_cards * 3 + 22)]

        for i, color in enumerate('wugrk'):
            coins_left = 4 - coins_1[i] - coins_2[i]
            color_strs.append(f"{coins_left}{color}")

        color_strs.append(f"{5 - coins_1[5] - coins_2[5]}y")

        # Make gem / coin strings
        s = ""
        for player in [1, 2]:
            if player == 1:
                s += f"""
                Player:
                """
                gems = state[(self.config.n_cards * 3): (self.config.n_cards * 3 + 5)]
                coins = state[(self.config.n_cards * 3 + 10): (self.config.n_cards * 3 + 16)]
            else:
                s += f"""
                Opponent:
                """
                gems = state[(self.config.n_cards * 3 + 5): (self.config.n_cards * 3 + 10)]
                coins = state[(self.config.n_cards * 3 + 16): (self.config.n_cards * 3 + 22)]

            for i, color in enumerate('wugrk'):
                if gems[i] > 0:
                    perma_gem_str = f"[{gems[i]}]"
                else:
                    perma_gem_str = ""
                s += f""" {color.upper()}: {perma_gem_str}{coins[i]} """
            s += f""" Y: {coins[5]} """

        # Reserved cards
        p1_cards = []
        p2_cards = []

        for i in np.where(state[self.config.n_cards:(self.config.n_cards * 2)] == 1)[0]:
            p1_cards.append(self.config.cards[i])
        for i in np.where(state[(self.config.n_cards * 2):(self.config.n_cards * 3)] == 1)[0]:
            p2_cards.append(self.config.cards[i])

        if just_print:
            print(f"""
            {tabs}Scores:
            {tabs}    1: {state[self.config.n_cards * 3 + 22]} | 2: {state[self.config.n_cards * 3 + 23]}
            {tabs}
            {tabs}Board:
            {tabs}    Level 3: {' | '.join([str(card) for card in level_3_cards])}
            {tabs}    Level 2: {' | '.join([str(card) for card in level_2_cards])}
            {tabs}    Level 1: {' | '.join([str(card) for card in level_1_cards])}
            {tabs}
            {tabs}Nobles:
            {tabs}      Available: {' | '.join([str(noble) for noble in np.array(self.config.nobles)[np.array(state[(self.config.n_cards * 3 + 25):(self.config.n_cards * 3 + 35)]).astype(bool)]])}
            {tabs}    
            {tabs}Coins left:
            {tabs}    {' '.join(color_strs)}
            {tabs}
            {tabs}Player coins / gems: 
            {tabs}    {s}
            {tabs}    
            {tabs}Reserved:
            {tabs}     Player 1: {' | '.join([str(card) for card in p1_cards])}
            {tabs}     Player 2: {' | '.join([str(card) for card in p2_cards])}
            """)
        else:
            self.log(f"""
            {tabs}Scores:
            {tabs}    1: {state[self.config.n_cards * 3 + 22]} | 2: {state[self.config.n_cards * 3 + 23]}
            {tabs}
            {tabs}Board:
            {tabs}    Level 3: {' | '.join([str(card) for card in level_3_cards])}
            {tabs}    Level 2: {' | '.join([str(card) for card in level_2_cards])}
            {tabs}    Level 1: {' | '.join([str(card) for card in level_1_cards])}
            {tabs}
            {tabs}Nobles:
            {tabs}      Available: {' | '.join([str(noble) for noble in np.array(self.config.nobles)[np.array(state[(self.config.n_cards * 3 + 25):(self.config.n_cards * 3 + 35)]).astype(bool)]])}
            {tabs}    
            {tabs}Coins left:
            {tabs}    {' '.join(color_strs)}
            {tabs}
            {tabs}Player coins / gems: 
            {tabs}    {s}
            {tabs}    
            {tabs}Reserved:
            {tabs}     Player 1: {' | '.join([str(card) for card in p1_cards])}
            {tabs}     Player 2: {' | '.join([str(card) for card in p2_cards])}
            """)


    def display_training_example(self, training_example):
        tabs = '\t\t'

        state = training_example[0]
        pi = training_example[1]
        r = training_example[2]

        # policy string
        policies = []
        for i, p in enumerate(pi):
            if p != 0:
                policies.append((i, p))
        policy_strs = [f"{self.convert_action_to_readable(el[0])}: {el[1]}" for el in sorted(policies, key=lambda x: x[1], reverse=True)]

        self.log(f"""
        {tabs}  POLICY: {', '.join(policy_strs)}
        {tabs}  R: {r}
        """)

        self.display_state_external(state)



    def display_game_state(self, m_or_b):
        start_time = time.time()
        tabs = '\t\t'
        self.log(f"""
        {tabs}Scores:
        {tabs}    1: {self.states[m_or_b].scores[1]} | 2: {self.states[m_or_b].scores[2]}
        {tabs}
        {tabs}Board:
        {tabs}        {self.beautify_board(m_or_b)}
        {tabs}
        {tabs}Nobles:
        {tabs}        {self.beautify_nobles(m_or_b)}
        {tabs}    
        {tabs}Coins left:
        {tabs}    {self.beautify_coins_left(m_or_b)}
        {tabs}
        {tabs}Player coins / gems: 
        {tabs}    {self.beautify_coins(m_or_b)}
        {tabs}    
        {tabs}Reserved:
        {tabs}        {self.beautify_reserved(m_or_b)}
        """)
        self.times['display_game_state'] += time.time() - start_time

    def color_order(self, color):
        d = {
            'w': 0,
            'u': 1,
            'g': 2,
            'r': 3,
            'k': 4
        }

        return d[color]

    def convert_input_action(self, input_action, player, m_or_b):
        if "BUY" in input_action.upper() and "RESERVE" in input_action.upper():
            match = re.search(r'\d+', input_action)
            if match:
                number = int(match.group(0))
                try:
                    card_i = np.where(self.states[m_or_b].reserved[player] == 1)[0][number]
                    action = card_i
                    return action
                except IndexError:
                    raise Exception(
                        f"Tried to get {number}th reserved card but only {np.where(self.states[m_or_b].reserved[player] == 1)[0]} reserved")

            else:
                raise Exception(f"Invalid input_action {input_action}")

        if "BUY" in input_action.upper() or "RESERVE" in input_action.upper():
            if "BUY" in input_action.upper():
                action_addition = 0

            if "RESERVE" in input_action.upper():
                if "RANDOM" in input_action.upper():
                    if "1" in input_action:
                        return self.config.n_cards * 2
                    elif "2" in input_action:
                        return self.config.n_cards * 2 + 1
                    elif "3" in input_action:
                        return self.config.n_cards * 2 + 2
                    else:
                        raise Exception(f"Invalid random reserve action: {input_action}")

                action_addition = self.config.n_cards

            match = re.search(r"\b\d+\s*,\s*\d+\b", input_action)

            if match:
                numbers_str = match.group()  # e.g. 1 , 4
                num1_str, num2_str = map(str.strip, numbers_str.split(','))
                level = int(num1_str)
                column = int(num2_str)

                if level not in [1, 2, 3] or column not in [0, 1, 2, 3]:
                    raise Exception(f"Invalid input_action {input_action}")
            else:
                raise Exception(f"Can't give command buy without a pair of numbers: {input_action}")

            if level == 1:
                lower_bound = 0
                upper_bound = self.config.n_level_1_cards

            elif level == 2:
                lower_bound = self.config.n_level_1_cards
                upper_bound = self.config.n_level_1_cards + self.config.n_level_2_cards
            elif level == 3:
                lower_bound = self.config.n_level_1_cards + self.config.n_level_2_cards
                upper_bound = self.config.n_level_1_cards + self.config.n_level_2_cards + self.config   .n_level_3_cards
            else:
                raise Exception(f"Invalid level {level}")

            card_i = np.where(self.states[m_or_b].board[lower_bound:upper_bound] == 1)[0][column]
            # print(f"column: {column}, card: {card_i + lower_bound}")

            action = card_i + lower_bound + action_addition  # type: ignore

            return action

        elif re.sub(r'[WUGRK]', '', input_action.upper()) == '':
            colors = input_action.lower()
            if len(colors) > 3:
                raise Exception(f"Invalid color string: {colors}")

            sorted_colors = ''.join(sorted(colors, key=self.color_order))
            return self.color_str_to_action_dict[sorted_colors]

        elif "NOTHING" in input_action.upper():
            return 213

        else:
            raise Exception(f"No recognized keyword in action: {input_action}")

    def display_valid_moves(self, player, m_or_b):
        tabs = "\t\t\t"
        self.log(f"""
        {tabs}VALID:
        {tabs}Level 1 buy:{np.where(self.current_valid_moves[:self.config.n_level_1_cards] == 1)[0]}
        {tabs}Level 2 buy:{np.where(self.current_valid_moves[self.config.n_level_1_cards:(self.config.n_level_1_cards + self.config.n_level_2_cards)] == 1)[0] + self.config.n_level_1_cards}
        {tabs}Level 3 buy:{np.where(self.current_valid_moves[(self.config.n_level_1_cards + self.config.n_level_2_cards):(self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards)] == 1)[0] + self.config.n_level_1_cards + self.config.n_level_2_cards}

        {tabs}Level 1 reserve:{np.where(self.current_valid_moves[self.config.n_cards:(self.config.n_cards + self.config.n_level_1_cards)] == 1)[0]}
        {tabs}Level 2 reserve:{np.where(self.current_valid_moves[(self.config.n_cards + self.config.n_level_1_cards):(self.config.n_cards + self.config.n_level_1_cards + self.config.n_level_2_cards)] == 1)[0] + self.config.n_level_1_cards}
        {tabs}Level 3 reserve:{np.where(self.current_valid_moves[(self.config.n_cards + self.config.n_level_1_cards + self.config.n_level_2_cards):(self.config.n_cards + self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards)] == 1)[0] + self.config.n_level_1_cards + self.config.n_level_2_cards}

        {tabs}Level 1 reserve random:{self.current_valid_moves[self.config.n_cards * 2]}
        {tabs}Level 2 reserve random:{self.current_valid_moves[self.config.n_cards * 2 + 1]}
        {tabs}Level 3 reserve random:{self.current_valid_moves[self.config.n_cards * 2 + 2]}

        {tabs}Taking 3 coins:{self.current_valid_moves[(self.config.n_cards * 2 + 3):(self.config.n_cards * 2 + 13)]}
        {tabs}Taking 2 coins:{self.current_valid_moves[(self.config.n_cards * 2 + 13):(self.config.n_cards * 2 + 23)]}
        {tabs}Taking 1 coins:{self.current_valid_moves[(self.config.n_cards * 2 + 23):(self.config.n_cards * 2 + 28)]}
        {tabs}Taking 2 coins of the same color:{self.current_valid_moves[(self.config.n_cards * 2 + 28):(self.config.n_cards * 2 + 33)]}
        {tabs}Taking no coins:{self.current_valid_moves[self.config.n_cards * 2 + 33]}
        """)


    def play_manual_game(self):

        self.display_game_state('main')

        current_player = 1
        while True:
            input_action = input(f"Take an action for player {current_player}: ")

            if "PRINT" in input_action.upper():
                if "BOARD" in input_action.upper():
                    print("Board")
                    print(f"Level 1:{self.states['main'].board[:self.config.n_level_1_cards]}")
                    print(f"Level 2:{self.states['main'].board[self.config.n_level_1_cards:self.config.n_level_1_cards + self.config.n_level_2_cards]}")
                    print(f"Level 3:{self.states['main'].board[self.config.n_level_1_cards + self.config.n_level_2_cards:self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards]}")

                if "RESERVED" in input_action.upper():
                    print("Player 1:")
                    print(f"Level 1:{self.states['main'].reserved[1][:self.config.n_level_1_cards]}")
                    print(f"Level 2:{self.states['main'].reserved[1][self.config.n_level_1_cards:self.config.n_level_1_cards + self.config.n_level_2_cards]}")
                    print(f"Level 3:{self.states['main'].reserved[1][self.config.n_level_1_cards + self.config.n_level_2_cards:self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards]}")

                    print("Player 2:")
                    print(f"Level 1:{self.states['main'].reserved[2][:self.config.n_level_1_cards]}")
                    print(f"Level 2:{self.states['main'].reserved[2][self.config.n_level_1_cards:self.config.n_level_1_cards + self.config.n_level_2_cards]}")
                    print(f"Level 3:{self.states['main'].reserved[2][self.config.n_level_1_cards + self.config.n_level_2_cards:self.config.n_level_1_cards + self.config.n_level_2_cards + self.config.n_level_3_cards]}")

                if "VALID" in input_action.upper():
                    self.display_valid_moves(current_player, 'main')

                continue

            try:
                action = self.convert_input_action(input_action, current_player, 'main')
            except Exception as e:
                print(f"""
                Invalid action: 
                    {str(e)}
                Please try again
                """)
                continue

            valid_moves = self.getValidMoves(None, current_player, 'main')
            if action not in np.where(valid_moves == 1)[0]:
                print(f"""
                Action {action} not possible in the game state. Please try again
                """)
                continue

            self.getNextState(None, current_player, action, 'main')

            game_end_result = self.getGameEnded(None, current_player, 'main')

            if game_end_result in [-1, 1]:
                if game_end_result == 1:
                    print(f"""
                        Player {current_player} has won!
                    """)
                else:
                    print(f"""
                        Player {self.switch_player(current_player)} has won!
                    """)
                self.display_game_state('main')
                break

            self.display_game_state('main')

            current_player = 3 - current_player

    def interpret_action(self, x):
        if x < self.config.n_cards:
            return f"Bought card {x}: {self.config.cards[x]}"
        elif x < self.config.n_cards * 2:
            return f"Reserved card {x - self.config.n_cards}: {self.config.cards[x - self.config.n_cards]}"
        elif self.config.n_cards * 2 <= x <= self.config.n_cards * 2 + 2:
            return f"Reserved random card from deck {x - self.config.n_cards * 2 + 1}"
        else:
            return f"Took coins {self.take_coins_action_dict[x]}"

    def play_random_game(self):

        m_to_b = 'main'

        turn = 1
        current_player = 1
        while True:
            print(f"TURN {turn}")
            self.display_game_state(m_to_b)

            valid_moves = self.getValidMoves(None, current_player, m_to_b)
            if np.sum(valid_moves) > 1:
                # Don't do nothing if there are multiple actions available
                action = np.random.choice(np.where(valid_moves[:213] == 1)[0])
            else:
                action = np.random.choice(np.where(valid_moves == 1)[0])

            if action not in np.where(valid_moves == 1)[0]:
                print(f"""
                Action {action} not possible in the game state. Please try again
                """)
                continue
            print(f"""Player {current_player} action: {self.interpret_action(action)}
                  """)

            self.getNextState(None, current_player, action, m_to_b)

            game_end_result = self.getGameEnded(None, current_player, m_to_b)

            if game_end_result in [-1, 1]:
                if game_end_result == 1:
                    print(f"""
                        Player {current_player} has won!
                    """)
                else:
                    print(f"""
                        Player {self.switch_player(current_player)} has won!
                    """)
                self.display_game_state(m_to_b)
                break

            current_player = 3 - current_player
            turn += 1
        return turn

    # @staticmethod
    # def display(board):
    #     n = board.shape[0]
    #     print("   ", end="")
    #     for y in range(n):
    #         print(y, end=" ")
    #     print("")
    #     print("-----------------------")
    #     for y in range(n):
    #         print(y, "|", end="")    # print the row #
    #         for x in range(n):
    #             piece = board[y][x]    # get the piece to print
    #             print(OthelloGame.square_content[piece], end=" ")
    #         print("|")
    #
    #     print("-----------------------")


if __name__ == "__main__":
    results = np.zeros(1000)
    for i in range(1000):
        game = SplendorGame()

        results[i] = game.play_random_game()
    print(f"""
        Min: {results.min()}
        Max: {results.max()}
        Avg: {results.mean()}
    """)
# manual_game()
