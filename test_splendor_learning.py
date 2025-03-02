import unittest
import logging
import os
import sys
import io
import numpy as np
from collections import deque
from contextlib import redirect_stdout
from typing import Callable, Any

from Coach import Coach
from splendor.SplendorGame import SplendorGame as Game
from splendor.NNet import NNetWrapper as nn
from utils import dotdict
from splendor.config import SplendorGameVariant

class QuietTestRunner:
    def __enter__(self):
        # Redirect stdout to devnull
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._devnull = open(os.devnull, 'w')
        sys.stdout = self._devnull
        sys.stderr = self._devnull
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stdout
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        self._devnull.close()

class TestSplendorLearning(unittest.TestCase):
    def setUp(self):
        # Configure logging to only show warnings and errors
        logging.basicConfig(level=logging.WARNING)
        
        # Suppress other loggers
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
        
        # Set up game parameters
        self.args = dotdict({
            'numIters': 15,  # We only need 15 iterations to test our hypothesis
            'numEps': 100,   # Number of complete self-play games per iteration
            'tempThreshold': 15,
            'updateThreshold': 0.55,
            'maxlenOfQueue': 200000,
            'numMCTSSims': 200,
            'arenaCompare': 40,  # Number of games to play during arena play
            'cpuct': 2,
            'game_type': SplendorGameVariant.LEVEL_0_2G1U,
            'checkpoint': './temp/',
            'load_model': False,
            'numItersForTrainExamplesHistory': 20,
        })
        
        # Track arena results and game lengths
        self.arena_results = []  # Will store (iteration, wins, losses, draws)
        self.game_lengths = []   # Will store game lengths for each arena game
        
        # Create game instance with all output suppressed
        self.game = Game(game_variant=self.args.game_type, verbose=False, output="file", debug_file_path="./temp/game.log")
        
        # Create neural network
        self.nnet = nn(self.game)
        
        # Create coach with all output suppressed
        self.coach = Coach(self.game, self.nnet, self.args, verbose=False, output="file", debug_file_path="./temp/coach.log")
        
        # Patch the arena playGame method to track game lengths
        self.original_playGame = self.coach.game.getGameEnded
        def patched_getGameEnded(board, player, m_or_b, print_to_terminal=False):
            result = self.original_playGame(board, player, m_or_b, print_to_terminal)
            if result != 0 and hasattr(self.game, 'states') and 'main' in self.game.states:
                # Only track completed games
                self.game_lengths.append(len(self.game.states['main'].gained_nobles[1]) + len(self.game.states['main'].gained_nobles[2]))
            return result
        
        self.coach.game.getGameEnded = patched_getGameEnded
        
    def test_learning_convergence(self):
        """Test that the learning process converges to optimal play within 15 iterations."""
        
        # Track consecutive successful iterations
        consecutive_successes = 0
        last_iteration = -1
        
        # Override learn method to track arena results
        def learn_with_tracking() -> bool:
            nonlocal consecutive_successes, last_iteration
            
            # Clear tracking for this run
            self.arena_results = []
            self.game_lengths = []
            
            accepted = True
            n_accepted = 0
            
            # Run learning process with progress tracking
            with QuietTestRunner():
                for i in range(1, self.args.numIters + 1):
                    print(f"\rIteration {i}/{self.args.numIters}", end="")
                    
                    # Store current length to check if new results were added
                    prev_len = len(self.arena_results)
                    
                    # Run one iteration
                    iteration_accepted = self.coach.learn_one_iteration(i, accepted, n_accepted)
                    
                    # Update acceptance state
                    if iteration_accepted:
                        accepted = True
                        n_accepted += 1
                    else:
                        accepted = False
                    
                    # Check results after iteration
                    if len(self.arena_results) > prev_len:
                        wins, losses, draws = self.arena_results[-1]
                        
                        # Check if this iteration meets our criteria
                        if wins == 20 and all(length <= 8 for length in self.game_lengths[prev_len*40:len(self.arena_results)*40]):
                            if len(self.arena_results) - 1 == last_iteration + 1:  # Check if consecutive
                                consecutive_successes += 1
                            else:
                                consecutive_successes = 1
                            last_iteration = len(self.arena_results) - 1
                        else:
                            consecutive_successes = 0
                            last_iteration = -1
                        
                        # If we've found 5 consecutive successful iterations, we're done
                        if consecutive_successes >= 5:
                            print("\nSuccess! Found 5 consecutive successful iterations.")
                            return True
            
            print("\nFailed to achieve target performance within iteration limit.")
            return False
        
        # Replace learn method with our tracking version
        setattr(self.coach, 'learn', learn_with_tracking)
        
        # Run the test
        success = self.coach.learn()
        
        # Assert that we achieved our goal
        self.assertTrue(success, "Failed to achieve 5 consecutive iterations with perfect arena performance and game length ≤ 6")

if __name__ == '__main__':
    # Suppress test runner output
    with redirect_stdout(io.StringIO()):
        unittest.main() 