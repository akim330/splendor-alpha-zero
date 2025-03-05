import logging
import os

from Logger import logger

import coloredlogs

from Coach import Coach
from splendor.SplendorGame import SplendorGame, SplendorGameFactory
from splendor.NNet import NNetWrapper
from splendor.config import args
from utils import *

log = logging.getLogger(__name__)

coloredlogs.install(level='INFO')  # Change this to DEBUG to see more info.


def main(verbose = False):
    try:
        # Get debug_file_path
        debug_log_folder = "./logs"

        existing_files = os.listdir(debug_log_folder)
        existing_log_files = [f for f in existing_files if f.endswith('.txt')]

        # Truncate file
        with open("./logs/init_state_examples.txt", 'w'):
            pass

        def get_num(s):
            try:
                return int(s.replace('.txt', ''))
            except:
                return 0
        existing_indices = [get_num(f) for f in existing_log_files]

        next_index = max(existing_indices, default=0) + 1
        debug_file_path = f"{debug_log_folder}/{next_index}.txt"

        # Set logger
        logger.configure(log_file_path=debug_file_path, verbose=args.verbose)

        print(f"Logging at {debug_file_path}")

        log.info('Loading %s...', SplendorGame.__name__)
        game = SplendorGame(game_variant=args.game_type, randomize = args.randomize)

        log.info('Loading %s...', NNetWrapper.__name__)
        nnet = NNetWrapper(input_size=game.getBoardSize(), action_size=game.getActionSize())

        if args.load_model:
            log.info('Loading checkpoint "%s/%s"...', args.load_folder_file[0], args.load_folder_file[1])
            nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])
        else:
            log.warning('Not loading a checkpoint!')

        log.info('Loading the Coach...')
        game_factory = SplendorGameFactory(game_variant=args.game_type, randomize_game=args.randomize)
        c = Coach(game_factory, nnet, args)

        if args.load_model:
            log.info("Loading 'trainExamples' from file...")
            c.loadTrainExamples()

        log.info('Starting the learning process 🎉')
        c.learn()
        
    except KeyboardInterrupt:
        log.info("\nTraining interrupted by user. Cleaning up...")
    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
        raise
    finally:
        log.info("Training session ended.")


if __name__ == "__main__":
    verbose = True
    main(verbose=verbose)
