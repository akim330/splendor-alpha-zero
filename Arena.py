import logging

import numpy as np
from tqdm import tqdm
from MCTS import MCTS
from splendor.SplendorGame import SplendorGame, SplendorGameFactory
from splendor.NNet import NNetWrapper
log = logging.getLogger(__name__)
from Logger import logger, LoggingSource
from utils import dotdict

class Arena():
    """
    An Arena class where any 2 agents can be pitted against each other.
    """

    def __init__(self, game_factory : SplendorGameFactory, old_nnet : NNetWrapper, new_nnet : NNetWrapper, args : dotdict):
        """
        Input:
            player 1,2: two functions that takes board as input, return action
            game: Game object
            display: a function that takes board as input and prints it (e.g.
                     display in othello/OthelloGame). Is necessary for verbose
                     mode.

        see othello/OthelloPlayers.py for an example. See pit.py for pitting
        human players/other baselines with each other.
        """
        self.game_factory = game_factory
        self.old_nnet = old_nnet
        self.new_nnet = new_nnet
        self.args = args

    def log(self, s, print_to_terminal=False):
        logger.log(s, source=LoggingSource.ARENA, print_to_terminal=print_to_terminal)

    def playGame(self, n_game, player1_nnet : NNetWrapper, player2_nnet : NNetWrapper):
        """
        Executes one episode of a game.

        Returns:
            either
                winner: player who won the game (1 if player1, -1 if player2)
            or
                draw result returned from the game that is neither 1, -1, nor 0.
        """
        game : SplendorGame = self.game_factory.create_game()
        game.reset_main()
        m_or_b = 'main'

        arenaCurPlayer = 1
        akCurPlayer = 1
        board = game.getInitBoard()
        it = 0
        while game.getGameEnded(akCurPlayer, m_or_b) == 0:
            it += 1
            # if verbose:
            #     assert self.display
            #     print("Turn ", str(it), "Player ", str(arenaCurPlayer))
            #     self.display(board)
            # print(f"Player: {curPlayer}")
            #action = players[curPlayer + 1](self.game.getCanonicalForm(board, curPlayer, m_or_b))

            player1_mcts = MCTS(game, player1_nnet, self.args)
            player2_mcts = MCTS(game, player2_nnet, self.args)

            players = [lambda player: np.argmax(player2_mcts.getActionProb(player, temp=0)), None, lambda player: np.argmax(player1_mcts.getActionProb(player, temp=0))]

            action = players[arenaCurPlayer + 1](akCurPlayer)
            self.log(f"ARENA GAME {n_game}: TURN {it} PLAYER {arenaCurPlayer} TAKES ACTION!: {action}")

            #valids = self.game.getValidMoves(self.game.getCanonicalForm(board, curPlayer, m_or_b), 1)
            valids = game.getValidMoves(akCurPlayer, m_or_b)

            if valids[action] == 0:
                log.error(f'Action {action} is not valid!')
                log.debug(f'valids = {valids}')
                assert valids[action] > 0
            board, akCurPlayer = game.getNextState(akCurPlayer, action, m_or_b, print_to_terminal = False)
            arenaCurPlayer = 1 if akCurPlayer == 1 else -1

        # print(f"Arena Game {n_game}: {it} turns, Result {game.getGameEnded(akCurPlayer, m_or_b)}")
        # if verbose:
        #     assert self.display
        #     print("Game over: Turn ", str(it), "Result ", str(self.game.getGameEnded(board, 1, m_or_b)))
        #     self.display(board)

        return arenaCurPlayer * game.getGameEnded(akCurPlayer, m_or_b, print_to_terminal = False) # type: ignore

    def playGames(self, num):
        """
        Plays num games in which player1 starts num/2 games and player2 starts
        num/2 games.

        Returns:
            oneWon: games won by player1
            twoWon: games won by player2
            draws:  games won by nobody
        """

        num = int(num / 2)
        oneWon = 0
        twoWon = 0
        draws = 0
        for i in tqdm(range(num), desc="Arena.playGames (1)"):
            if i == 0:
                logger.set_verbose(True)
            else:
                logger.set_verbose(False)
            
            self.log(f"###########################################")
            self.log(f"###### ARENA GAME {i} for player 1 ########")
            self.log(f"###########################################")

            gameResult = self.playGame(n_game = i, player1_nnet = self.old_nnet, player2_nnet = self.new_nnet)
            if gameResult == 1:
                oneWon += 1
            elif gameResult == -1:
                twoWon += 1
            else:
                draws += 1

        # self.player1, self.player2 = self.player2, self.player1

        for i in tqdm(range(num), desc="Arena.playGames (2)"):
            if i == 0:
                logger.set_verbose(True)
            else:
                logger.set_verbose(False)

            self.log(f"###########################################")
            self.log(f"###### ARENA GAME {i} for player 2 ########")
            self.log(f"###########################################")

            gameResult = self.playGame(n_game = i, player1_nnet = self.new_nnet, player2_nnet = self.old_nnet)
            if gameResult == -1:
                oneWon += 1
            elif gameResult == 1:
                twoWon += 1
            else:
                draws += 1

        return oneWon, twoWon, draws
