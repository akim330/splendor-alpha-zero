import logging
import os
import sys
import time
from collections import deque
from pickle import Pickler, Unpickler
from random import shuffle

import numpy as np
from tqdm import tqdm

from Arena import Arena
from MCTS import MCTS

log = logging.getLogger(__name__)


class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """

    def __init__(self, game, nnet, args, verbose, output = 'print', debug_file_path = None, display_time = False, display_all = False):
        self.game = game
        self.nnet = nnet
        self.pnet = self.nnet.__class__(self.game)  # the competitor network
        self.args = args
        self.mcts = MCTS(self.game, self.nnet, self.args, verbose = verbose, display_time=display_time)
        self.trainExamplesHistory = []  # history of examples from args.numItersForTrainExamplesHistory latest iterations
        self.skipFirstSelfPlay = False  # can be overriden in loadTrainExamples()
        self.verbose = verbose

        self.output = output
        self.debug_file_path = debug_file_path

        self.times = {}

        self.reset_times()

        self.display_time = display_time
        self.display_all = display_all

    def reset_times(self):
        self.times = {
            'misc': 0,
            'get_action_prob': 0,
            'get_next_state': 0,
            'get_game_ended': 0
        }

    def log(self, s):
        if self.output == 'file':
            with open(self.debug_file_path, 'a') as f:
                f.write(f"{s}\n")

        elif self.output == 'print':
            print(s)

    def executeEpisode(self):
        """
        This function executes one episode of self-play, starting with player 1.
        As the game is played, each turn is added as a training example to
        trainExamples. The game is played till the game ends. After the game
        ends, the outcome of the game is used to assign values to each example
        in trainExamples.

        It uses a temp=1 if episodeStep < tempThreshold, and thereafter
        uses temp=0.

        Returns:
            trainExamples: a list of examples of the form (canonicalBoard, currPlayer, pi,v)
                           pi is the MCTS informed policy vector, v is +1 if
                           the player eventually won the game, else -1.
        """
        trainExamples = []
        board = self.game.getInitBoard()
        self.curPlayer = 1
        episodeStep = 0

        # Here, game updates on the main branch (i.e. not hypothetical moves which is in MCTS)
        m_or_b = 'main'
        # Restart the game
        self.game.reset_main()

        # self.log("Coach: Starting a new game of self-play!")

        # Run the game until someone wins
        while True:
            episodeStep += 1
            time0 = time.time()

            canonicalBoard = self.game.getCanonicalForm(board, self.curPlayer, m_or_b)

            temp = int(episodeStep < self.args.tempThreshold)
            if self.verbose:
                self.log(f"Coach: TURN {episodeStep}: let's see the state")
                self.game.display_game_state(m_or_b)

            #pi = self.mcts.getActionProb(canonicalBoard, temp=temp)
            time1 = time.time()
            pi = self.mcts.getActionProb(self.curPlayer, temp=temp)
            time2 = time.time()
            sym = self.game.getSymmetries(canonicalBoard, pi)
            for b, p in sym:
                trainExamples.append([b, self.curPlayer, p, None])

            action = np.random.choice(len(pi), p=pi)

            strs = []
            for i, a in enumerate(pi):
                if pi[i] != 0:
                    strs.append(f"({i}, {pi[i]})")

            if self.verbose:
                self.log(f"\t***** MCTS: DONE for one action! Based on final probs, take action: {action} *****")
                self.log(f"\tpi: {', '.join(strs)}")

            board, self.curPlayer = self.game.getNextState(board, self.curPlayer, action, m_or_b)
            time3 = time.time()

            r = self.game.getGameEnded(board, self.curPlayer, m_or_b)

            time4 = time.time()

            self.times['misc'] += time1 - time0
            self.times['get_action_prob'] += time2 - time1
            self.times['get_next_state'] += time3 - time2
            self.times['get_game_ended'] += time4 - time3

            if r == -2:
                # Game ended on 2 consecutive do-nothings so whoever has the highest score wins

                if self.game.states[m_or_b].scores[self.curPlayer] > self.game.states[m_or_b].scores[3 - self.curPlayer]:
                    r = 1
                elif self.game.states[m_or_b].scores[3 - self.curPlayer] - self.game.states[m_or_b].scores[self.curPlayer]:
                    r = -1
                else:
                    return [(x[0], x[2], -1) for x in trainExamples]

                return [(x[0], x[2], r * ((-1) ** (x[1] != self.curPlayer))) for x in trainExamples]


            elif r != 0:
                return [(x[0], x[2], r * ((-1) ** (x[1] != self.curPlayer))) for x in trainExamples]

    def explainTrainExamples(self, iterationTrainExamples):
        for i, trainExample in enumerate(iterationTrainExamples):
            self.log(f"########### TRAIN EXAMPLE {i} ###############")
            self.game.display_training_example(trainExample)


    def learn(self):
        """
        Performs numIters iterations with numEps episodes of self-play in each
        iteration. After every iteration, it retrains neural network with
        examples in trainExamples (which has a maximum length of maxlenofQueue).
        It then pits the new neural network against the old one and accepts it
        only if it wins >= updateThreshold fraction of games.
        """

        for i in range(1, self.args.numIters + 1):
            # bookkeeping
            log.info(f'Starting Iter #{i} ...')
            self.log(f"##################################")
            self.log(f"##### COACH GLOBAL ROUND {i} #####")
            self.log(f"##################################")


            # examples of the iteration
            if not self.skipFirstSelfPlay or i > 1:
                iterationTrainExamples = deque([], maxlen=self.args.maxlenOfQueue)

                for j in tqdm(range(self.args.numEps), desc="Self Play"):
                    if self.display_all:
                        self.verbose = True
                    elif j != self.args.numEps - 1:
                        self.verbose = False

                    else:
                        self.verbose = True
                    self.game.verbose = self.verbose

                    # Truncate file
                    with open(self.debug_file_path, 'w'):
                        pass

                    self.log(f"##### COACH SELF-PLAY GAME {j} #####")


                    self.mcts = MCTS(self.game, self.nnet, self.args, verbose=self.verbose, output = self.output, debug_file_path=self.debug_file_path, display_time=self.display_time)  # reset search tree

                    # Run an episode of self-play
                    start_time = time.time()
                    iterationTrainExamples += self.executeEpisode()
                    if self.display_time:
                        print(f"ONE GAME: {round(time.time() - start_time, 2 )}s")
                        print(self.times)
                        print(self.game.times)
                        print(self.mcts.times)
                        self.reset_times()

                # save the iteration examples to the history
                self.trainExamplesHistory.append(iterationTrainExamples)

                self.explainTrainExamples(iterationTrainExamples)

            # If too many iterationTrainExamples stored, remove oldest entry in trainExampleshistory
            if len(self.trainExamplesHistory) > self.args.numItersForTrainExamplesHistory:
                log.warning(
                    f"Removing the oldest entry in trainExamples. len(trainExamplesHistory) = {len(self.trainExamplesHistory)}")
                self.trainExamplesHistory.pop(0)
            # backup history to a file
            # NB! the examples were collected using the model from the previous iteration, so (i-1)  
            self.saveTrainExamples(i - 1)

            # shuffle examples before training
            trainExamples = []
            for e in self.trainExamplesHistory:
                trainExamples.extend(e)
            shuffle(trainExamples)

            # training new network, keeping a copy of the old one
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            self.pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            pmcts = MCTS(self.game, self.pnet, self.args, verbose=self.verbose, output = self.output, debug_file_path=self.debug_file_path)

            self.nnet.train(trainExamples)
            nmcts = MCTS(self.game, self.nnet, self.args, verbose=self.verbose, output = self.output, debug_file_path=self.debug_file_path)

            log.info('PITTING AGAINST PREVIOUS VERSION')

            self.log(f"##########################")
            self.log(f"##########################")
            self.log(f"##### STARTING ARENA #####")
            self.log(f"##########################")
            self.log(f"##########################\n")


            # self.mcts.verbose = False
            # self.game.verbose = False
            arena = Arena(lambda player, verbose_override: np.argmax(pmcts.getActionProb(player, temp=0, verbose_override=verbose_override)),
                          lambda player, verbose_override: np.argmax(nmcts.getActionProb(player, temp=0, verbose_override=verbose_override)),
                          self.game,
                          verbose = self.verbose,
                          output= self.output,
                          debug_file_path= self.debug_file_path)
            pwins, nwins, draws = arena.playGames(self.args.arenaCompare)

            # if self.verbose:
            #     self.mcts.verbose = True
            #     self.game.verbose = True



            log.info('NEW/PREV WINS : %d / %d ; DRAWS : %d' % (nwins, pwins, draws))
            if pwins + nwins == 0 or float(nwins) / (pwins + nwins) < self.args.updateThreshold:
                log.info('REJECTING NEW MODEL')
                self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            else:
                log.info('ACCEPTING NEW MODEL')
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename=self.getCheckpointFile(i))
                self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')

                self.log(f"""######### NN TEST ##############""")

                # Pick random initial state

                # Pick random mid state

                # Pick mid position obviously favoring player

                # Pick mid position obviously favoring opponent

                # Pick end position very close to victory

                # Pick end position very close to defeat

                self.log(f"""######### NN TEST ##############""")


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
