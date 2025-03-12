import logging
import concurrent.futures
import numpy as np
from tqdm import tqdm
from MCTS import MCTS
from splendor.SplendorGame import SplendorGame, SplendorGameFactory
from splendor.NNet import NNetWrapper
log = logging.getLogger(__name__)
from Logger import logger, LoggingSource
from utils import dotdict
import os

def execute_arena_game_worker(game_factory_args, nnet1_args, nnet2_args, args, n_game, verbose=False):
    """
    Standalone worker function for parallel execution of arena games.
    Creates its own instances of required objects to avoid pickling issues.
    """
    # Create new instances inside the worker process
    game_factory = SplendorGameFactory(game_factory_args['game_variant'], game_factory_args['randomize'])
    player1_nnet = NNetWrapper(nnet1_args['input_size'], nnet1_args['action_size'])
    player2_nnet = NNetWrapper(nnet2_args['input_size'], nnet2_args['action_size'])
    
    # Load neural network weights
    player1_nnet.load_checkpoint(nnet1_args['checkpoint_folder'], nnet1_args['checkpoint_file'])
    player2_nnet.load_checkpoint(nnet2_args['checkpoint_folder'], nnet2_args['checkpoint_file'])
    
    # Create game instance
    game = game_factory.create_game()
    game.reset_main()
    m_or_b = 'main'

    # Set up logging for this process
    if verbose:
        logger.set_verbose(verbose)

    logger.log(f"###########################################", source=LoggingSource.ARENA)
    logger.log(f"###### ARENA GAME {n_game} ########", source=LoggingSource.ARENA)
    logger.log(f"###########################################", source=LoggingSource.ARENA)

    arenaCurPlayer = 1
    akCurPlayer = 1
    board = game.getInitBoard()
    it = 0

    while game.getGameEnded(akCurPlayer, m_or_b) == 0:
        it += 1
        player1_mcts = MCTS(game, player1_nnet, args)
        player2_mcts = MCTS(game, player2_nnet, args)

        players = [lambda player: np.argmax(player2_mcts.getActionProb(player, temp=0)), None, lambda player: np.argmax(player1_mcts.getActionProb(player, temp=0))]

        action = players[arenaCurPlayer + 1](akCurPlayer)
        logger.log(f"ARENA GAME {n_game}: TURN {it} PLAYER {arenaCurPlayer} TAKES ACTION!: {action}", source=LoggingSource.ARENA)

        valids = game.getValidMoves(akCurPlayer, m_or_b)

        if valids[action] == 0:
            log.error(f'Action {action} is not valid!')
            log.debug(f'valids = {valids}')
            assert valids[action] > 0
        board, akCurPlayer = game.getNextState(akCurPlayer, action, m_or_b, print_to_terminal = False)
        arenaCurPlayer = 1 if akCurPlayer == 1 else -1

    return arenaCurPlayer * game.getGameEnded(akCurPlayer, m_or_b, print_to_terminal = False)

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
        
        # Set up number of workers
        if 'numWorkers' in self.args and self.args.numWorkers is not None:
            self.num_workers = self.args.numWorkers
        else:
            self.num_workers = min(4, os.cpu_count() or 4)
            
        self.pool = None
        
        # Prepare arguments that will be passed to worker processes
        self.game_factory_args = {
            'game_variant': game_factory.game_variant,
            'randomize': game_factory.randomize_game
        }

    def init_pool(self):
        if self.pool is None:
            self.pool = concurrent.futures.ProcessPoolExecutor(max_workers=self.num_workers)
            
    def shutdown_pool(self):
        if self.pool:
            self.pool.shutdown(wait=True)
            self.pool = None

    def log(self, s, print_to_terminal=False):
        logger.log(s, source=LoggingSource.ARENA, print_to_terminal=print_to_terminal)

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

        try:
            self.init_pool()
            if not self.pool:
                raise RuntimeError("Failed to initialize process pool")

            # First half: old_nnet (player1) vs new_nnet (player2)
            nnet1_args = {
                'input_size': self.game_factory.get_board_size(),
                'action_size': self.game_factory.get_action_size(),
                'checkpoint_folder': self.args.checkpoint,
                'checkpoint_file': 'temp.pth.tar'
            }
            
            nnet2_args = {
                'input_size': self.game_factory.get_board_size(),
                'action_size': self.game_factory.get_action_size(),
                'checkpoint_folder': self.args.checkpoint,
                'checkpoint_file': 'best.pth.tar'
            }

            # Save current network states
            self.old_nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            self.new_nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')

            # Submit first batch of games
            futures = []
            for i in range(num):
                verbose = i == 0
                future = self.pool.submit(
                    execute_arena_game_worker,
                    self.game_factory_args,
                    nnet1_args,
                    nnet2_args,
                    self.args,
                    i,
                    verbose
                )
                futures.append((i, future))

            # Process first batch results
            for i, future in tqdm(futures, desc="Arena.playGames (1)"):
                try:
                    gameResult = future.result()
                    if gameResult == 1:
                        oneWon += 1
                    elif gameResult == -1:
                        twoWon += 1
                    else:
                        draws += 1
                except Exception as e:
                    log.error(f"Error in game {i}: {str(e)}")
                    continue

            # Second half: new_nnet (player1) vs old_nnet (player2)
            # Swap the checkpoint files in the args
            nnet1_args['checkpoint_file'] = 'best.pth.tar'
            nnet2_args['checkpoint_file'] = 'temp.pth.tar'

            # Submit second batch of games
            futures = []
            for i in range(num):
                verbose = i == 0
                future = self.pool.submit(
                    execute_arena_game_worker,
                    self.game_factory_args,
                    nnet1_args,
                    nnet2_args,
                    self.args,
                    i,
                    verbose
                )
                futures.append((i, future))

            # Process second batch results
            for i, future in tqdm(futures, desc="Arena.playGames (2)"):
                try:
                    gameResult = future.result()
                    if gameResult == -1:
                        oneWon += 1
                    elif gameResult == 1:
                        twoWon += 1
                    else:
                        draws += 1
                except Exception as e:
                    log.error(f"Error in game {i}: {str(e)}")
                    continue

        finally:
            self.shutdown_pool()

        return oneWon, twoWon, draws
