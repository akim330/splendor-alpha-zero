import logging
import os

import coloredlogs

from Coach import Coach
from splendor.SplendorGame import SplendorGame as Game
from splendor.NNet import NNetWrapper as nn
from utils import *

log = logging.getLogger(__name__)

coloredlogs.install(level='INFO')  # Change this to DEBUG to see more info.

args = dotdict({
    'numIters': 1000,
    'numEps': 100,              # Number of complete self-play games to simulate during a new iteration.
    'tempThreshold': 15,        #
    'updateThreshold': 0.6,     # During arena playoff, new neural net will be accepted if threshold or more of games are won.
    'maxlenOfQueue': 200000,    # Number of game examples to train the neural networks.
    'numMCTSSims': 25,          # Number of games moves for MCTS to simulate.
    'arenaCompare': 40,         # Number of games to play during arena play to determine if new net will be accepted.
    'cpuct': 1,

    'checkpoint': './temp/',
    'load_model': False,
    'load_folder_file': ('/dev/models/8x100x50','best.pth.tar'),
    'numItersForTrainExamplesHistory': 20,

})


def main(verbose = False):
    # Get debug_file_path
    debug_log_folder = "./logs"
    output = "file"
    display_time = False
    display_all = False

    existing_files = os.listdir(debug_log_folder)
    existing_log_files = [f for f in existing_files if f.endswith('.txt')]

    def get_num(s):
        try:
            return int(s.replace('.txt', ''))
        except:
            return 0
    existing_indices = [get_num(f) for f in existing_log_files]

    next_index = max(existing_indices, default=0) + 1
    debug_file_path = f"{debug_log_folder}/{next_index}.txt"

    print(f"Logging at {debug_file_path}")

    log.info('Loading %s...', Game.__name__)
    g = Game(verbose=verbose, output = output, debug_file_path = debug_file_path, display_time = display_time)

    log.info('Loading %s...', nn.__name__)
    nnet = nn(g, verbose=verbose, output = output, debug_file_path = debug_file_path)

    if args.load_model:
        log.info('Loading checkpoint "%s/%s"...', args.load_folder_file[0], args.load_folder_file[1])
        nnet.load_checkpoint(args.load_folder_file[0], args.load_folder_file[1])
    else:
        log.warning('Not loading a checkpoint!')

    log.info('Loading the Coach...')
    c = Coach(g, nnet, args, verbose=verbose, output = output, debug_file_path = debug_file_path, display_time = display_time, display_all=display_all)

    if args.load_model:
        log.info("Loading 'trainExamples' from file...")
        c.loadTrainExamples()

    log.info('Starting the learning process 🎉')
    c.learn()


if __name__ == "__main__":
    verbose = True
    main(verbose=verbose)
