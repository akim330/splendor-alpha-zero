#!/usr/bin/env python

from splendor.config import args, SplendorGameVariant
from Coach import Coach
from utils import dotdict
from splendor.NNet import NNetWrapper
from splendor.SplendorGame import SplendorGameFactory
import time
import logging
import argparse

def test_parallel_coach(num_workers=None, num_games=8):
    """Test the parallelized Coach implementation."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a game factory
    game_factory = SplendorGameFactory(SplendorGameVariant.VANILLA, True)
    
    # Create neural network
    nnet = NNetWrapper(game_factory.get_board_size(), game_factory.get_action_size())
    
    # Set up testing args
    test_args = dotdict({
        'numEps': num_games,      # Number of games to run
        'tempThreshold': 15,
        'maxlenOfQueue': 200000,
        'numItersForTrainExamplesHistory': 20,
        'arenaCompare': 40,
        'updateThreshold': 0.6,
        'debug_self_play_with_temp_0': False,
        'load_examples_from_file': False,
        'dont_use_loaded_trainExamples': True,
        'train_examples_file': "",
        'checkpoint': "./temp/",
        'numIters': 1,            # Only need 1 iteration for testing
        'numWorkers': num_workers  # Configurable number of worker processes
    })
    
    # Create Coach instance
    coach = Coach(game_factory=game_factory, nnet=nnet, args=test_args)
    
    # Test parallelized execution
    start_time = time.time()
    coach.learn_one_iteration(1, True, 0)
    end_time = time.time()
    
    # Print results
    print(f"Completed {test_args.numEps} games in {end_time - start_time:.2f} seconds")
    print(f"Using {coach.num_workers} worker processes")
    
    return coach

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test parallel Coach implementation')
    parser.add_argument('--workers', type=int, help='Number of worker processes to use')
    parser.add_argument('--games', type=int, default=8, help='Number of games to run')
    args = parser.parse_args()
    
    test_parallel_coach(args.workers, args.games) 