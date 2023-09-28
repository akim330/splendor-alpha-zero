import logging
import math
import time

import numpy as np
import pandas as pd

from splendor.config import level_1_cards, level_2_cards, level_3_cards

n_cards = len(level_1_cards) + len(level_2_cards) + len(level_3_cards)

EPS = 1e-8

log = logging.getLogger(__name__)

def round_to_1(x):
    if x == 0:
        return 0
    elif pd.isnull(x):
        return 'none'
    return round(x, -int(np.floor(np.log10(abs(x)))))

def round_to_3(x):
    if x == 0:
        return 0
    elif pd.isnull(x):
        return 'none'
    return  round(x, -int(np.floor(np.log10(abs(x)))) + 2)

class MCTS():
    """
    This class handles the MCTS tree.
    """

    def __init__(self, game, nnet, args, verbose = False, output = "file", debug_file_path = None, display_time = False):
        self.game = game
        self.nnet = nnet
        self.args = args
        self.Qsa = {}  # stores Q values for s,a (as defined in the paper)
        self.Nsa = {}  # stores #times edge s,a was visited
        self.Ns = {}  # stores #times board s was visited
        self.Ps = {}  # stores initial policy (returned by neural net)

        self.Es = {}  # stores game.getGameEnded ended for board s
        self.Vs = {}  # stores game.getValidMoves for board s
        self.verbose = verbose

        self.output = output

        self.debug_file_path = debug_file_path

        self.times = {}
        self.reset_times()

        self.display_time = display_time

    def reset_times(self):
        self.times = {
            'misc1': 0,
            'misc2': 0,
            'get_next_state': 0,
            'get_game_ended': 0,
            'nn': 0,
            'valid': 0
        }

    def log(self, s):
        if self.verbose:
            if self.output == 'file':
                with open(self.debug_file_path, 'a') as f:
                    f.write(f"{s}\n")

            elif self.output == 'print':
                print(s)

    def getActionProb(self, player, temp=1, verbose_override = None):
        """
        This function performs numMCTSSims simulations of MCTS starting from
        canonicalBoard.

        Returns:
            probs: a policy vector where the probability of the ith action is
                   proportional to Nsa[(s,a)]**(1./temp)
        """

        past_verbose = self.verbose

        if verbose_override is not None:
            self.verbose = verbose_override

        if self.verbose:
            self.log(f"MCTS: Get the best action by running MCTS {self.args.numMCTSSims} times")

        action_start_time = time.time()

        # Perform MCTS search numMCTSSims times
        for i in range(self.args.numMCTSSims):
            if self.verbose:
                self.log(f"\n\t########## MCTS: Search iteration {i} #########\n")
                self.log(f"\t\tMCTS: Reloading new branch")

            self.game.reset_branch()
            if self.verbose:
                tabs = "\t\t"
                canonicalBoard = self.game.getCanonicalForm(None, player, 'branch')
                # self.log(f"""
                # {tabs}\t board: {canonicalBoard[:90]}
                # {tabs}\t reserved 1: {canonicalBoard[90:180]}
                # {tabs}\t reserved 2: {canonicalBoard[180:270]}
                # {tabs}\t perma_gems 1:  {canonicalBoard[270:275]}
                # {tabs}\t perma_gems 2:  {canonicalBoard[275:280]}
                # {tabs}\t coins 1:  {canonicalBoard[280:286]}
                # {tabs}\t coins 2:  {canonicalBoard[286:292]}
                # {tabs}\t score 1:  {canonicalBoard[292]}
                # {tabs}\t score 2:  {canonicalBoard[293]}
                # {tabs}\t started_first:  {canonicalBoard[294]}
                # {tabs}\t nobles:  {canonicalBoard[295:305]}
                # """)

            self.search(player, depth = 0, did_nothing_last_recursion = False)



        # On main branch of the game since we're not taking any steps, just displaying things
        m_or_b = 'main'

        canonicalBoard = self.game.getCanonicalForm(None, player, m_or_b)
        s = self.game.stringRepresentation(player, m_or_b)
        counts = [self.Nsa[(s, a)] if (s, a) in self.Nsa else 0 for a in range(self.game.getActionSize())]

        if self.display_time:
            print(f"Finding an action took: {round(time.time() - action_start_time, 3)}s")

        self.verbose = past_verbose

        if temp == 0:
            bestAs = np.array(np.argwhere(counts == np.max(counts))).flatten()
            bestA = np.random.choice(bestAs)
            probs = [0] * len(counts)
            probs[bestA] = 1
            return probs

        counts = [x ** (1. / temp) for x in counts]
        counts_sum = float(sum(counts))
        probs = [x / counts_sum for x in counts]
        return probs

    def search(self, player, depth, did_nothing_last_recursion):
        """
        This function performs one iteration of MCTS. It is recursively called
        till a leaf node is found. The action chosen at each node is one that
        has the maximum upper confidence bound as in the paper.

        Once a leaf node is found, the neural network is called to return an
        initial policy P and a value v for the state. This value is propagated
        up the search path. In case the leaf node is a terminal state, the
        outcome is propagated up the search path. The values of Ns, Nsa, Qsa are
        updated.

        NOTE: the return values are the negative of the value of the current
        state. This is done since v is in [-1,1] and if v is the value of a
        state for the current player, then its value is -v for the other player.

        Returns:
            v: the negative of the value of the current canonicalBoard
        """
        tabs = '\t\t'

        m_or_b = 'branch'

        self.log(f"{tabs}##### DEPTH {depth} #####")

        time0 = time.time()

        if self.verbose and depth > 0:
            self.game.display_game_state(m_or_b)

        # Q: why does this function return negative of value of the current state?
        # A: because it's called recursively by the previous state. That previous state
        # is associated with the other player, so the value returned to them is the opposite

        # Get canonical board (board from the point of view of this player)
        canonicalBoard = self.game.getCanonicalForm(None, player, m_or_b)
        # print(f"canon canon: {canonicalBoard}")
        # Convert game state to a string
        s = self.game.stringRepresentation(player, m_or_b)
        # print(f"stringy ouput: {s}")

        time1 = time.time()

        self.game.set_current_valid_moves(player, m_or_b)

        time2 = time.time()

        # See if we had consecutive do nothings
        if self.game.states[m_or_b].consecutive_do_nothings >= 2:
            return -1

        # Check if we know whether s is a terminal state
        if s not in self.Es:
            # If we don't know, then figure out if s is a terminal state
            self.Es[s] = self.game.getGameEnded(None, player, m_or_b)
        # If s is a terminal state, get the value (+1 if win or -1 if lost)
        if self.Es[s] != 0:
            self.log(f"{tabs}MCTS: s is terminal")
            # Return negative of the value (see above for explanation)
            return -self.Es[s]

        time3 = time.time()

        # Do we have an NN-returned policy calculated for this tree
        if s not in self.Ps:
            self.log(f"{tabs}MCTS: Don't have an NN-policy for s so calculating now")
            # self.log(f"canonicalForm: {canonicalBoard}")
            # self.log(f"s: {s}")
                # print(f"stringy ouput 2: {s}")

                # for s in self.Ps:
                #     print(f"{tabs}\t key: {s}")
            # We don't have a policy calculated (means it's a leaf node since we haven't explored down here yet for this tree)
            nn_start_time = time.time()
            # Calculate NN policy (probabilities assigned to actions based on goodness)
            self.Ps[s], v = self.nnet.predict(canonicalBoard)
            # self.log(f"NN output: {self.Ps[s]}")

            self.times['nn'] += time.time()  - nn_start_time

            # Valid moves for this state (canonicalBoard means just from the point of view of the current player, so "player" is just 1)
            valids = self.game.current_valid_moves
            # print(f"DEBUG 4: {valids}")

            # Only take the probabilities for the valid moves
            self.Ps[s] = self.Ps[s] * valids  # masking invalid moves

            # Renormalize
            sum_Ps_s = np.sum(self.Ps[s])
            if sum_Ps_s > 0:
                self.Ps[s] /= sum_Ps_s  # renormalize
            else:
                # if all valid moves were masked make all valid moves equally probable

                # NB! All valid moves may be masked if either your NNet architecture is insufficient or you've gotten overfitting or something else.
                # If you have got dozens or hundreds of these messages you should pay attention to your NNet and/or training process.   
                log.error("All valid moves were masked, doing a workaround.")
                self.Ps[s] = self.Ps[s] + valids
                self.Ps[s] /= np.sum(self.Ps[s])
            # print(f"stringy ouput 3: {s}")

            # Store valid moves per state
            self.Vs[s] = valids
            # print(f"STORING for player {player}, {m_or_b}")
            # print(f"KEY: {s}")
            # print(f"CANONICAL: {canonicalBoard}")
            # print(f"STORED: {self.Vs[s]}")

            # Initialize N at 0 because this is the first time we're seeing this state for this tree
            # (will get incremented to 1 later in this iteration)
            self.Ns[s] = 0
            self.log(f"{tabs}MCTS: Returning value {-v}")
            return -v

        self.log(f"{tabs}MCTS: already have NN-policy ")

        valids = self.Vs[s]

        if np.sum(valids) > 1:
            # 213
            valids[n_cards * 2 + 33] = 0
        # print(f"DEBUG 6 for player{player} and {m_or_b}: {valids}")

        cur_best = -float('inf')
        best_act = -1

        # self.log(f"{tabs}MCTS: these are the valid moves")

        time4 = time.time()

        if self.verbose:
            self.game.display_valid_moves(player, m_or_b)

        # pick the action with the highest upper confidence bound

        strs = []
        us = np.ones(self.game.getActionSize()) * -99
        # print(f"VALIDS: {valids}")
        for a in range(self.game.getActionSize()):
            if valids[a]:
                if (s, a) in self.Qsa:
                    us[a] = self.Qsa[(s, a)] + self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s]) / (
                            1 + self.Nsa[(s, a)])

                    strs.append(
                        f"({a}, Q:{round_to_3(self.Qsa[(s, a)])}, Ps:{round_to_3(self.Ps[s][a])}, Ns:{round_to_1(self.Ns[s])}, Nsa:{round_to_1(self.Nsa[(s, a)])}, u:{round_to_3(us[a])})")

                else:
                    us[a] = self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s] + EPS)  # Q = 0 ?

                    strs.append(
                        f"({a}, Q:none, Ps:{round_to_3(self.Ps[s][a])}, Ns:{round_to_1(self.Ns[s])}, u:{round_to_3(us[a])})")


        time5 = time.time()

        # Find the maximum value in the array
        max_val = np.max(us)
        assert max_val != -99, "Max value is still -99"

        # Find the indices with the maximum value
        max_indices = np.where(us == max_val)[0]

        # Randomly select one best act
        best_act = np.random.choice(max_indices)

        self.log(f"{tabs}MCTS UCT: {', '.join(strs)}")
        self.log(f"{tabs}Taking best action by UCT: {best_act}, leading to new state:")

        a = best_act
        next_s, next_player = self.game.getNextState(None, player, a, m_or_b)
        next_s = self.game.getCanonicalForm(next_s, next_player, m_or_b)

        if a == n_cards * 2 + 33:
            if did_nothing_last_recursion:
                return -1
            else:
                did_nothing_last_recursion = True
        else:
            did_nothing_last_recursion = False

        time6 = time.time()

        self.times['misc1'] += (time1 - time0)
        self.times['misc2'] += (time5 - time4)
        self.times['get_next_state'] += time6 - time5
        self.times['get_game_ended'] += time3 - time2
        self.times['valid'] += time2 - time1


        # Recurrence
        # This will call search for the next child down. For now, this particular search call is paused here.
        # There will be a chain of unfinished "search" calls all the way down the tree
        # Finally when it gets to a leaf node, a value v will be returned. Then we can go back up the tree and
        # execute the next code
        v = self.search(next_player, depth + 1, did_nothing_last_recursion=did_nothing_last_recursion)

        # If we've seen this state-action pair in the Q matrix, update the value
        if (s, a) in self.Qsa:
            self.Qsa[(s, a)] = (self.Nsa[(s, a)] * self.Qsa[(s, a)] + v) / (self.Nsa[(s, a)] + 1)
            self.Nsa[(s, a)] += 1
        # If we haven't seen, then just make Q = v
        else:
            self.Qsa[(s, a)] = v
            self.Nsa[(s, a)] = 1

        self.Ns[s] += 1

        return -v
