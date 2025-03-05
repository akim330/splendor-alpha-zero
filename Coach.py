from Logger import logger, LoggingSource
from splendor.NNet import NNetWrapper
from splendor.SplendorGame import SplendorGame, SplendorGameFactory
import os
import sys
import time
import signal
from collections import deque
from pickle import Pickler, Unpickler
from random import shuffle
from splendor.config import SplendorGameVariant, args
import concurrent.futures
import numpy as np
from tqdm import tqdm

from Arena import Arena
from MCTS import MCTS

import logging

from utils import dotdict

log = logging.getLogger(__name__)

def execute_one_game_worker(game_factory_args, nnet_args, coach_args, game_num, nn_version, verbose=False, print_to_terminal=False, temp_override=None):
    """
    Standalone worker function for parallel execution of games.
    Creates its own instances of required objects to avoid pickling issues.
    """
    # Create new instances inside the worker process
    game_factory = SplendorGameFactory(game_factory_args['game_variant'], game_factory_args['randomize'])
    nnet = NNetWrapper(nnet_args['input_size'], nnet_args['action_size'])
    
    # Load neural network weights if provided
    if 'checkpoint_folder' in nnet_args and 'checkpoint_file' in nnet_args:
        nnet.load_checkpoint(nnet_args['checkpoint_folder'], nnet_args['checkpoint_file'])
    
    # Create game instance
    game = game_factory.create_game()
    
    # Set up logging for this process
    if verbose:
        logger.set_verbose(verbose)

    if temp_override == 0:
        logger.log("########## Playing one round of self-play with temp = 0 ##########", 
                  source=LoggingSource.COACH, 
                  print_to_terminal=True)
    
    logger.log(f"##### COACH SELF-PLAY ROUND | NN VERSION {nn_version} | GAME {game_num} #####",
               source=LoggingSource.COACH)
    
    # Run an episode of self-play
    start_time = time.time()
    train_examples = execute_one_game(game_factory, game, nnet, coach_args, nn_version, print_to_terminal, temp_override)
    game_time = time.time() - start_time
    
    return game_num, train_examples, game_time

def execute_one_game(game_factory, game, nnet, args, nn_version, print_to_terminal=False, temp_override=None):
    """
    Standalone function to execute one game of self-play.
    """
    trainExamples = []
    board = game.getInitBoard()
    curPlayer = 1
    episodeStep = 0
    times = {'misc': 0.0, 'get_action_prob': 0.0, 'get_next_state': 0.0, 'get_game_ended': 0.0}

    # Here, game updates on the main branch (i.e. not hypothetical moves which is in MCTS)
    m_or_b = 'main'
    # Restart the game
    game.reset_main()

    # Run the game until someone wins
    while True:
        episodeStep += 1
        time0 = time.time()

        # For every move, create a new MCTS object
        mcts = MCTS(game, nnet, args)
        
        canonicalBoard = game.getCanonicalForm(board, curPlayer, m_or_b)
        
        # Get state value before taking action
        _, state_value = nnet.predict(canonicalBoard)

        temp = int(episodeStep < args.tempThreshold) if temp_override is None else temp_override
        logger.log(f"Coach: TURN {episodeStep}: let's see the state", source=LoggingSource.COACH)
        game.display_game_state(m_or_b)

        time1 = time.time()
        pi = mcts.getActionProb(curPlayer, temp=temp)
        time2 = time.time()
        sym = game.getSymmetries(canonicalBoard, pi)
        for b, p in sym:
            trainExamples.append([b, curPlayer, p, None])

        action = np.random.choice(len(pi), p=pi)
        p_action = pi[action]

        action_prob_strs = []
        for i, p in sorted(list(enumerate(pi)), key=lambda pair: pair[1], reverse=True):
            if p != 0:
                action_prob_strs.append(f"({game.convert_action_to_readable(i)}, {round(p, 3)})")

        logger.log(f"***** MCTS (NN V{nn_version} | TURN {episodeStep} | temp = {temp}): pi: {', '.join(action_prob_strs[:3])} => 4: {action} (p = {round(p_action * 100, 3)}%), state_value = {round(state_value, 3)} *****", 
                  source=LoggingSource.COACH,
                  print_to_terminal=print_to_terminal)
        logger.log(f"\tpi: {', '.join(action_prob_strs)}", source=LoggingSource.COACH)

        board, curPlayer = game.getNextState(curPlayer, action, m_or_b, print_to_terminal=True)
        time3 = time.time()

        r = game.getGameEnded(curPlayer, m_or_b, print_to_terminal=True)

        time4 = time.time()

        times['misc'] += time1 - time0
        times['get_action_prob'] += time2 - time1
        times['get_next_state'] += time3 - time2
        times['get_game_ended'] += time4 - time3

        if r == -2:
            # Game ended on 2 consecutive do-nothings so whoever has the highest score wins
            if game.states[m_or_b].scores[curPlayer] > game.states[m_or_b].scores[3 - curPlayer]:
                r = 1
            elif game.states[m_or_b].scores[3 - curPlayer] > game.states[m_or_b].scores[curPlayer]:
                r = -1
            else:
                return [(x[0], x[2], 0) for x in trainExamples]

            return [(x[0], x[2], r * ((-1) ** (x[1] != curPlayer))) for x in trainExamples]

        elif r != 0:
            return [(x[0], x[2], r * ((-1) ** (x[1] != curPlayer))) for x in trainExamples]


class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """

    def __init__(self, game_factory : SplendorGameFactory, nnet : NNetWrapper, args : dotdict):
        self.game_factory = game_factory
        self.nnet = nnet
        self.pnet = self.nnet.__class__(game_factory.get_board_size(), game_factory.get_action_size())
        self.args = args
        self.trainExamplesHistory = []
        self.skipFirstSelfPlay = False

        self.first_action = None
        self.first_nn_value = np.empty(0)
        self.first_prob_strs = None
        self.first_temp = None
        self.first_action_dict = {}
        self.times = {}
        self.arena_results = []

        self.reset_times()
        
        if 'numWorkers' in self.args and self.args.numWorkers is not None:
            self.num_workers = min(self.args.numWorkers, self.args.numEps)
        else:
            self.num_workers = min(self.args.numEps, os.cpu_count() or 4)
            
        self.pool = None
        
        # Prepare arguments that will be passed to worker processes
        self.game_factory_args = {
            'game_variant': game_factory.game_variant,
            'randomize': game_factory.randomize_game
        }
        
        self.nnet_args = {
            'input_size': game_factory.get_board_size(),
            'action_size': game_factory.get_action_size(),
            'checkpoint_folder': None,  # Will be set before each iteration
            'checkpoint_file': None     # Will be set before each iteration
        }

    def init_pool(self):
        if self.pool is None:
            self.pool = concurrent.futures.ProcessPoolExecutor(max_workers=self.num_workers)
            
    def shutdown_pool(self):
        if self.pool:
            self.pool.shutdown(wait=False)
            self.pool = None

    def handle_keyboard_interrupt(self, signum, frame):
        log.info("\nReceived keyboard interrupt. Shutting down workers...")
        self.shutdown_pool()
        raise KeyboardInterrupt

    def reset_times(self):
        self.times = {
            'misc': 0.0,
            'get_action_prob': 0.0,
            'get_next_state': 0.0,
            'get_game_ended': 0.0
        }

    def log(self, s, print_to_terminal = False):
        logger.log(s, source=LoggingSource.COACH, print_to_terminal=print_to_terminal)

    def learn_one_iteration(self, num_iter, accepted=True, n_accepted=0):
        """Execute a single iteration of the learning process."""
        self.debug_file_path_suffix = f"_{(num_iter // 5) * 5}_{(num_iter // 5) * 5 + 4}"

        if num_iter % 5 == 0:
            logger.clear_log_file()

        # bookkeeping
        log.info(f'Starting Iter #{num_iter} ...')
        self.log(f"##################################")
        self.log(f"##### COACH GLOBAL ROUND {num_iter} #####")
        self.log(f"##################################")

        sorted_data = dict(sorted(self.first_action_dict.items(), key=lambda item: item[1][2], reverse=True))

        self.log(f"""
        ########### NEW ROUND #############
        {sorted_data}
        """)

        if not self.skipFirstSelfPlay or num_iter > 1:
            iterationTrainExamples = deque([], maxlen=self.args.maxlenOfQueue)

            original_handler = signal.signal(signal.SIGINT, self.handle_keyboard_interrupt)

            try:
                self.init_pool()
                if not self.pool:
                    raise RuntimeError("Failed to initialize process pool")

                # Update neural network args with current weights path
                self.nnet_args['checkpoint_folder'] = self.args.checkpoint
                self.nnet_args['checkpoint_file'] = 'temp.pth.tar'
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')

                # Submit all tasks to the executor
                futures = []
                for game_num in range(self.args.numEps):
                    verbose = game_num == self.args.numEps - 1

                    future = self.pool.submit(
                        execute_one_game_worker,
                        self.game_factory_args,
                        dict(self.nnet_args),  # Create a copy of the dictionary
                        self.args,
                        game_num,
                        n_accepted,
                        verbose=verbose,
                        print_to_terminal=True
                    )
                    futures.append((game_num, future))
                
                # Process results as they complete
                for game_num, future in tqdm([(gn, f) for gn, f in futures], 
                                          total=self.args.numEps, 
                                          desc="Self Play"):
                    try:
                        _, train_examples, game_time = future.result()
                        if train_examples:
                            if game_num == 0:  # Only explain the first game's examples
                                self.explainTrainExamples(train_examples)
                            iterationTrainExamples += train_examples
                    except (KeyboardInterrupt, concurrent.futures.CancelledError):
                        log.info("Processing interrupted by user")
                        raise KeyboardInterrupt
                    except Exception as e:
                        log.error(f"Error in game {game_num}: {str(e)}")
                        continue

            except KeyboardInterrupt:
                log.info("\nKeyboard interrupt received. Cleaning up...")
                raise
            
            finally:
                # Restore original signal handler and clean up pool
                signal.signal(signal.SIGINT, original_handler)
                self.shutdown_pool()

            if self.args.debug_self_play_with_temp_0:
                # Just for debugging, play one round of self-play with temp = 0
                _, debug_examples, _ = execute_one_game_worker(
                    self.game_factory_args,
                    self.nnet_args,
                    self.args,
                    0,
                    n_accepted,
                    verbose=True,
                    print_to_terminal=True,
                    temp_override=0
                )

            # save the iteration examples to the history
            self.trainExamplesHistory.append(iterationTrainExamples)

            # If too many examples, remove the oldest ones
            if len(self.trainExamplesHistory) > self.args.numItersForTrainExamplesHistory:
                log.warning(
                    f"Removing the oldest entry in trainExamples. len(trainExamplesHistory) = {len(self.trainExamplesHistory)}")
                self.trainExamplesHistory.pop(0)

            # Backup history to a file
            self.saveTrainExamples(num_iter - 1)

            # Shuffle examples before training
            trainExamples = []
            for e in self.trainExamplesHistory:
                trainExamples.extend(e)
            shuffle(trainExamples)

            # Training new network, keeping a copy of the old one
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            self.pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')

            log.info('TRAINING NEW MODEL')
            self.nnet.train(trainExamples)

            log.info('PITTING AGAINST PREVIOUS VERSION')
            self.log(f"###############################################################")
            self.log(f"###############################################################")
            self.log(f"##### STARTING ARENA (iter {num_iter} | NN V{n_accepted}) #####")
            self.log(f"###############################################################")
            self.log(f"###############################################################\n")

            arena = Arena(game_factory=self.game_factory, old_nnet=self.pnet, new_nnet=self.nnet, args=self.args)
            old_wins, new_wins, draws = arena.playGames(self.args.arenaCompare)
            
            # Store arena results
            self.arena_results.append((new_wins, old_wins, draws))

            log.info('NEW/PREV WINS : %d / %d ; DRAWS : %d' % (new_wins, old_wins, draws))
            if old_wins + new_wins == 0 or float(new_wins) / (old_wins + new_wins) < self.args.updateThreshold:
                log.info('REJECTING NEW MODEL')
                self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
                return False
            else:
                log.info('ACCEPTING NEW MODEL')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename=self.getCheckpointFile(num_iter))
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')
                return True

    def explainTrainExamples(self, iterationTrainExamples):
        # There will only be winner data
        # Each piece of train data is (canonicalBoard, pi, z) and ONLY the z has the winner (-1 or 1)
        for i, trainExample in enumerate(iterationTrainExamples):
            self.log(f"########### TRAIN EXAMPLE {i} ###############")
            self.game_factory.display_training_example(trainExample)

    def learn(self):
        """
        Performs numIters iterations with numEps episodes of self-play in each
        iteration. After every iteration, it retrains neural network with
        examples in trainExamples (which has a maximum length of maxlenofQueue).
        It then pits the new neural network against the old one and accepts it
        only if it wins >= updateThreshold fraction of games.
        """
        accepted = True
        n_accepted = 0
        
        # Initialize arena_results list if not already present
        if not hasattr(self, 'arena_results'):
            self.arena_results = []

        for num_iter in range(1, self.args.numIters + 1):
            self.learn_one_iteration(num_iter, accepted, n_accepted)
            
            # Update acceptance state based on last arena result
            if self.arena_results and self.arena_results[-1][0] >= self.args.arenaCompare * self.args.updateThreshold:
                accepted = True
                n_accepted += 1
            else:
                accepted = False

    def getCheckpointFile(self, iteration):
        return 'checkpoint_' + str(iteration) + '.pth.tar'

    def saveTrainExamples(self, iteration):
        folder = self.args.checkpoint
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, self.getCheckpointFile(iteration) + ".examples")
        with open(filename, "wb+") as f:
            Pickler(f).dump(self.trainExamplesHistory)
        f.closed

    def loadTrainExamples(self):
        modelFile = os.path.join(self.args.load_folder_file[0], self.args.load_folder_file[1])
        examplesFile = modelFile + ".examples"
        if not os.path.isfile(examplesFile):
            log.warning(f'File "{examplesFile}" with trainExamples not found!')
            r = input("Continue? [y|n]")
            if r != "y":
                sys.exit()
        else:
            log.info("File with trainExamples found. Loading it...")
            with open(examplesFile, "rb") as f:
                self.trainExamplesHistory = Unpickler(f).load()
            log.info('Loading done!')

            # examples based on the model were already collected (loaded)
            self.skipFirstSelfPlay = True
