from Logger import logger, LoggingSource
from splendor.SplendorGame import SplendorGame
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

import logging

log = logging.getLogger(__name__)

class Coach():
    """
    This class executes the self-play + learning. It uses the functions defined
    in Game and NeuralNet. args are specified in main.py.
    """

    def __init__(self, game, nnet, args):
        self.game : SplendorGame = game
        self.nnet = nnet
        self.pnet = self.nnet.__class__(self.game)  # the competitor network
        self.args = args
        self.mcts = MCTS(self.game, self.nnet, self.args)
        self.trainExamplesHistory = []  # history of examples from args.numItersForTrainExamplesHistory latest iterations
        self.skipFirstSelfPlay = False  # can be overriden in loadTrainExamples()

        self.first_action = None
        self.first_nn_value = np.empty(0)
        self.first_prob_strs = None
        self.first_temp = None

        self.first_action_dict = {}

        self.times = {}

        self.reset_times()


    def reset_times(self):
        self.times = {
            'misc': 0.0,
            'get_action_prob': 0.0,
            'get_next_state': 0.0,
            'get_game_ended': 0.0
        }

    def log(self, s, print_to_terminal = False):
        logger.log(s, source=LoggingSource.COACH, print_to_terminal=print_to_terminal)

    def executeEpisode(self, nn_version, new_nn_version = False, temp_override = None):
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
            
            # Get state value before taking action
            _, state_value = self.nnet.predict(canonicalBoard)

            temp = int(episodeStep < self.args.tempThreshold) if temp_override is None else temp_override
            self.log(f"Coach: TURN {episodeStep}: let's see the state")
            self.game.display_game_state(m_or_b)

            #pi = self.mcts.getActionProb(canonicalBoard, temp=temp)
            time1 = time.time()
            pi : list[float] = self.mcts.getActionProb(self.curPlayer, temp=temp)
            time2 = time.time()
            sym = self.game.getSymmetries(canonicalBoard, pi)
            for b, p in sym:
                trainExamples.append([b, self.curPlayer, p, None])

            action : int = np.random.choice(len(pi), p=pi)
            p_action : float = pi[action]

            action_prob_strs : list[str] = []
            for i, p in sorted(list(enumerate(pi)), key = lambda pair: pair[1], reverse=True):
                if p != 0:
                    action_prob_strs.append(f"({self.game.convert_action_to_readable(i)}, {round(p, 3)})")

            self.log(f"***** MCTS (NN V{nn_version} | TURN {episodeStep} | temp = {temp}): pi: {', '.join(action_prob_strs[:3])} => 4: {action} (p = {round(p_action * 100, 3)}%), state_value = {round(state_value, 3)} *****", print_to_terminal = new_nn_version)
            self.log(f"\tpi: {', '.join(action_prob_strs)}")

            board, self.curPlayer = self.game.getNextState(board, self.curPlayer, action, m_or_b, print_to_terminal = True)
            time3 = time.time()

            if episodeStep == 1:
                self.first_temp = temp
                self.first_prob_strs = action_prob_strs
                self.first_action = action
                self.first_nn_value = self.nnet.predict(self.game.getCanonicalForm(None, self.curPlayer, m_or_b))
                # self.log(f"NN (next line) on state: {self.game.getCanonicalForm(None, self.curPlayer, m_or_b)}", debug_file_path="./logs/init_state_examples.txt")

            r = self.game.getGameEnded(board, self.curPlayer, m_or_b, print_to_terminal = True)

            time4 = time.time()

            self.times['misc'] += time1 - time0
            self.times['get_action_prob'] += time2 - time1
            self.times['get_next_state'] += time3 - time2
            self.times['get_game_ended'] += time4 - time3

            if r == -2:
                # Game ended on 2 consecutive do-nothings so whoever has the highest score wins

                if self.game.states[m_or_b].scores[self.curPlayer] > self.game.states[m_or_b].scores[3 - self.curPlayer]:
                    r = 1
                elif self.game.states[m_or_b].scores[3 - self.curPlayer] > self.game.states[m_or_b].scores[self.curPlayer]:
                    r = -1
                else:
                    return [(x[0], x[2], 0) for x in trainExamples]

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

        self.game.reset_main()

        if accepted:
            new_nn_version = True
            pi, v = self.nnet.predict(self.game.getCanonicalForm(None, 1, "main"))
            # policy string
            policies = []
            for i, p in enumerate(pi):
                if p != 0:
                    policies.append((i, p))
            policy_strs = [f"{self.game.convert_action_to_readable(el[0])}: {round(el[1], 3)}" for el in
                           sorted(policies, key=lambda x: x[1], reverse=True)][:5]

            self.log(f"""
            ########### NEW NN VERSION {n_accepted} !!!!!! #############
            
            Policy: {','.join(policy_strs)}
                on state: {self.game.getCanonicalForm(None, 1, "main")}
            """)
        else:
            new_nn_version = False

        sorted_data = dict(sorted(self.first_action_dict.items(), key=lambda item: item[1][2], reverse=True))

        self.log(f"""
        ########### NEW ROUND #############
        {sorted_data}
        """)

        # examples of the iteration
        if not self.skipFirstSelfPlay or num_iter > 1:
            iterationTrainExamples = deque([], maxlen=self.args.maxlenOfQueue)

            for game_num in tqdm(range(self.args.numEps), desc="Self Play"):
                if game_num != self.args.numEps - 1:
                    logger.set_verbose(False)
                else:
                    logger.set_verbose(True)

                self.log(f"##### COACH SELF-PLAY ROUND {num_iter} | NN VERSION {n_accepted} | GAME {game_num} #####")

                self.mcts = MCTS(self.game, self.nnet, self.args)  # reset search tree

                # Run an episode of self-play
                start_time = time.time()
                currentTrainExamples = self.executeEpisode(nn_version=n_accepted, new_nn_version=True)

                pi = currentTrainExamples[0][1]
                r = currentTrainExamples[0][2]

                # policy string
                policies = []
                for i, p in enumerate(pi):
                    if p != 0:
                        policies.append((i, p))
                policy_strs = [f"{self.game.convert_action_to_readable(el[0])}: {round(el[1], 3)}" for el in
                               sorted(policies, key=lambda x: x[1], reverse=True)][:2]


                action_s = self.game.convert_action_to_readable(self.first_action)

                if action_s in self.first_action_dict:
                    if r == 1:
                        wins = self.first_action_dict[action_s][1] + 1
                    else:
                        wins = self.first_action_dict[action_s][1]
                    total = self.first_action_dict[action_s][0] + 1
                    self.first_action_dict[action_s] = (total, wins, round(wins/total, 2), self.first_nn_value[1] * -1)
                else:
                    if r == 1:
                        wins = 1
                    else:
                        wins = 0
                    self.first_action_dict[action_s] = (1, wins, round(wins/1, 2), self.first_nn_value[1] * -1)

                self.log(f"""R: {r}, A: {action_s}, temp: {self.first_temp}, NN: {self.first_nn_value[1] * -1}""")
                self.log(f"\t{self.first_prob_strs}")


                # self.log(f"""
                # POLICY: {', '.join(policy_strs)},
                # R: {r}
                # """, debug_file_path="./logs/init_state_examples.txt")

                self.explainTrainExamples(currentTrainExamples)
                iterationTrainExamples += currentTrainExamples

            if self.args.debug_self_play_with_temp_0:
                self.log("########## Playing one round of self-play with temp = 0 ##########", print_to_terminal = True)
                # Just for debugging, play one round of self-play with temp = 0
                self.executeEpisode(nn_version=n_accepted, new_nn_version=True, temp_override=0)

            # save the iteration examples to the history
            self.trainExamplesHistory.append(iterationTrainExamples)


        # If too many iterationTrainExamples stored, remove oldest entry in trainExampleshistory
        if len(self.trainExamplesHistory) > self.args.numItersForTrainExamplesHistory:
            log.warning(
                f"Removing the oldest entry in trainExamples. len(trainExamplesHistory) = {len(self.trainExamplesHistory)}")
            self.trainExamplesHistory.pop(0)
        # backup history to a file
        # NB! the examples were collected using the model from the previous iteration, so (i-1)  
        self.saveTrainExamples(num_iter - 1)

        # shuffle examples before training
        trainExamples = []
        for e in self.trainExamplesHistory:
            trainExamples.extend(e)
        shuffle(trainExamples)

        # training new network, keeping a copy of the old one
        self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
        self.pnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
        pmcts = MCTS(self.game, self.pnet, self.args)

        self.nnet.train(trainExamples)
        nmcts = MCTS(self.game, self.nnet, self.args)

        self.game.reset_main()

        pi, v = self.nnet.predict(self.game.getCanonicalForm(None, 1, "main"))
        # self.log(self.game.getCanonicalForm(None, 1, "main"), debug_file_path="./logs/init_state_examples.txt")
        # policy string
        policies = []
        for i, p in enumerate(pi):
            if p != 0:
                policies.append((i, p))
        policy_strs = [f"{self.game.convert_action_to_readable(el[0])}: {round(el[1], 3)}" for el in
                       sorted(policies, key=lambda x: x[1], reverse=True)][:5]

        state = np.concatenate(
            [self.game.states["main"].board, self.game.states['main'].reserved[1], self.game.states["main"].reserved[2],
             list(self.game.states["main"].perma_gems[1].values()), list(self.game.states["main"].perma_gems[2].values()),
             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 2, 0],
             [0, 0, -1],
             self.game.states["main"].nobles_board
             ], dtype=int)

        _, v_taking_kk = self.nnet.predict(state)

        self.log(f"""
        Post-train Policy: {','.join(policy_strs)}
        Value of taking kk: {v_taking_kk * -1}
        """)

        # self.log(f"""
        # Post-train Policy: {','.join(policy_strs)}
        #     on state: {self.game.getCanonicalForm(None, 1, "main")}
        # Value of taking kk: {v_taking_kk * -1}
        #     on state: {state}
        # """, debug_file_path="./logs/init_state_examples.txt")

        log.info('PITTING AGAINST PREVIOUS VERSION')

        self.log(f"###############################################################")
        self.log(f"###############################################################")
        self.log(f"##### STARTING ARENA (iter {num_iter} | NN V{n_accepted}) #####")
        self.log(f"###############################################################")
        self.log(f"###############################################################\n")


        # self.mcts.verbose = False
        # self.game.verbose = False
        arena = Arena(lambda player: np.argmax(pmcts.getActionProb(player, temp=0)),
                      lambda player: np.argmax(nmcts.getActionProb(player, temp=0)),
                      self.game)
        pwins, nwins, draws = arena.playGames(self.args.arenaCompare)
        
        # Store arena results
        self.arena_results.append((nwins, pwins, draws))

        # if self.verbose:
        #     self.mcts.verbose = True
        #     self.game.verbose = True



        log.info('NEW/PREV WINS : %d / %d ; DRAWS : %d' % (nwins, pwins, draws))
        if pwins + nwins == 0 or float(nwins) / (pwins + nwins) < self.args.updateThreshold:
            log.info('REJECTING NEW MODEL')
            self.nnet.load_checkpoint(folder=self.args.checkpoint, filename='temp.pth.tar')
            return False
        else:
            log.info('ACCEPTING NEW MODEL')
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename=self.getCheckpointFile(num_iter))
            self.nnet.save_checkpoint(folder=self.args.checkpoint, filename='best.pth.tar')

            self.log(f"""######### NN TEST ##############""")

            # Pick random initial state

            # Pick random mid state

            # Pick mid position obviously favoring player

            # Pick mid position obviously favoring opponent

            # Pick end position very close to victory

            # Pick end position very close to defeat

            self.log(f"""######### NN TEST ##############""")

            return True

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
