import logging

from tqdm import tqdm
from splendor.SplendorGame import SplendorGame

log = logging.getLogger(__name__)
from Logger import logger, LoggingSource

class Arena():
    """
    An Arena class where any 2 agents can be pitted against each other.
    """

    def __init__(self, player1, player2, game: SplendorGame):
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
        self.player1 = player1
        self.player2 = player2
        self.game = game

    def log(self, s, print_to_terminal=False):
        logger.log(s, source=LoggingSource.ARENA, print_to_terminal=print_to_terminal)

    def playGame(self, n_game):
        """
        Executes one episode of a game.

        Returns:
            either
                winner: player who won the game (1 if player1, -1 if player2)
            or
                draw result returned from the game that is neither 1, -1, nor 0.
        """
        game = SplendorGame()
        self.game.reset_main()
        m_or_b = 'main'

        players = [self.player2, None, self.player1]
        arenaCurPlayer = 1
        akCurPlayer = 1
        board = self.game.getInitBoard()
        it = 0
        while self.game.getGameEnded(board, akCurPlayer, m_or_b) == 0:
            it += 1
            # if verbose:
            #     assert self.display
            #     print("Turn ", str(it), "Player ", str(arenaCurPlayer))
            #     self.display(board)
            # print(f"Player: {curPlayer}")
            #action = players[curPlayer + 1](self.game.getCanonicalForm(board, curPlayer, m_or_b))
            action = players[arenaCurPlayer + 1](akCurPlayer)
            self.log(f"ARENA GAME {n_game}: TURN {it} PLAYER {arenaCurPlayer} TAKES ACTION!: {action}")

            #valids = self.game.getValidMoves(self.game.getCanonicalForm(board, curPlayer, m_or_b), 1)
            valids = self.game.getValidMoves(None, akCurPlayer, m_or_b)

            if valids[action] == 0:
                log.error(f'Action {action} is not valid!')
                log.debug(f'valids = {valids}')
                assert valids[action] > 0
            board, akCurPlayer = self.game.getNextState(board, akCurPlayer, action, m_or_b, print_to_terminal = False)
            arenaCurPlayer = 1 if akCurPlayer == 1 else -1

        # if verbose:
        #     assert self.display
        #     print("Game over: Turn ", str(it), "Result ", str(self.game.getGameEnded(board, 1, m_or_b)))
        #     self.display(board)

        return arenaCurPlayer * self.game.getGameEnded(None, akCurPlayer, m_or_b, print_to_terminal = False) # type: ignore

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

            gameResult = self.playGame(n_game = i)
            if gameResult == 1:
                oneWon += 1
            elif gameResult == -1:
                twoWon += 1
            else:
                draws += 1

        self.player1, self.player2 = self.player2, self.player1

        for i in tqdm(range(num), desc="Arena.playGames (2)"):
            if i == 0:
                logger.set_verbose(True)
            else:
                logger.set_verbose(False)

            self.log(f"###########################################")
            self.log(f"###### ARENA GAME {i} for player 2 ########")
            self.log(f"###########################################")

            gameResult = self.playGame(n_game = i)
            if gameResult == -1:
                oneWon += 1
            elif gameResult == 1:
                twoWon += 1
            else:
                draws += 1

        return oneWon, twoWon, draws
