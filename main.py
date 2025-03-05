import logging
import os

from Logger import logger

import coloredlogs

from Coach import Coach
from splendor.SplendorGame import SplendorGame as Game
from splendor.NNet import NNetWrapper as nn
from utils import *
from splendor.config import SplendorGameVariant

log = logging.getLogger(__name__)

coloredlogs.install(level='INFO')  # Change this to DEBUG to see more info.

args = dotdict({
    'numIters': 1000,
    'numEps': 100,              # Number of complete self-play games to simulate during a new iteration.
    'tempThreshold': 15,        # 
    'updateThreshold': 0.55,     # During arena playoff, new neural net will be accepted if threshold or more of games are won.
    'maxlenOfQueue': 200000,    # Number of game examples to train the neural networks.
    'numMCTSSims': 200,          # Number of games moves for MCTS to simulate.
    'arenaCompare': 40,         # Number of games to play during arena play to determine if new net will be accepted.
    'cpuct': 2,
    'game_type': SplendorGameVariant.LEVEL_1_GRK,
    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,
    'verbose': True,
    'debug_self_play_with_temp_0': True,
    'randomize': False
})


def main(verbose = False):
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

    log.info('Loading %s...', Game.__name__)
    g = Game(game_variant=args.game_type, randomize = args.randomize)

    log.info('Loading %s...', nn.__name__)
    nnet = nn(g)

    if args.load_model:
        log.info('Loading checkpoint "%s/%s"...', args.load_folder_file[0], args.load_folder_file[1])
        nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])
    else:
        log.warning('Not loading a checkpoint!')

    log.info('Loading the Coach...')
    c = Coach(g, nnet, args)

    if args.load_model:
        log.info("Loading 'trainExamples' from file...")
        c.loadTrainExamples()

    log.info('Starting the learning process 🎉')
    c.learn()


if __name__ == "__main__":
    verbose = True
    main(verbose=verbose)
