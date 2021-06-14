# ===============================================================================
# Imports
# ===============================================================================

import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP
import time
from collections import defaultdict

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5


# ===============================================================================
# Player
# ===============================================================================

class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_k_turns, k)
        self.clock = time.process_time()

        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.
        self.turns_remaining_in_round = self.k
        self.time_remaining_in_round = self.time_per_k_turns
        self.time_for_current_move = self.time_remaining_in_round / self.turns_remaining_in_round - 0.05
        self.time_factor = (self.k + 1) * (self.k / 2)

    def update_time_turn(self):
        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()
        turn_number = self.k - self.turns_remaining_in_round + 1
        self.time_for_current_move = (((self.turns_remaining_in_round / self.time_factor)
                                       * self.time_remaining_in_round - 0.05)
                                      if self.turns_remaining_in_round > 1 else self.time_for_current_move - 0.05)
        # if self.turns_remaining_in_round > 1:
        #     self.time_for_current_move = self.time_remaining_in_round / (turn_number + 1)
        if len(possible_moves) == 1:
            self.update_time_turn()
            return possible_moves[0]

        current_depth = 1
        last_runtime = 0
        last_remaining_time = 0
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                              self.selective_deepening_criterion)

        # Iterative deepening until the time runs out.
        while True:
            depth_factor = current_depth / 10

            remaining_time = self.time_for_current_move - (time.process_time() - self.clock)
            last_runtime = last_remaining_time - remaining_time
            # print( 'going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}, moves number: {},
            # remain turns {}'.format( current_depth, remaining_time, prev_alpha, best_move, len(possible_moves),
            # self.turns_remaining_in_round))

            try:
                # if last run time + a depth factor is more than the time left, there is no point on trying,
                # it's way better to use the time left for another turn
                if (last_runtime + depth_factor) >= remaining_time and (self.turns_remaining_in_round > 1):
                    # print("last time remain: " + str(last_remaining_time) + " time remain: " + str(
                    #     remaining_time) + " last run time: " + str(last_runtime))
                    break
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    self.time_for_current_move - (time.process_time() - self.clock))

            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                # print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1
            last_remaining_time = remaining_time

        self.update_time_turn()

        return best_move

    def utility(self, state):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        piece_counts = defaultdict(lambda: 0)
        for loc_val in state.board.values():
            if loc_val != EM:
                piece_counts[loc_val] += 1

        opponent_color = OPPONENT_COLOR[self.color]

        my_u = ((PAWN_WEIGHT * piece_counts[PAWN_COLOR[self.color]]) +
                (KING_WEIGHT * piece_counts[KING_COLOR[self.color]]))
        op_u = ((PAWN_WEIGHT * piece_counts[PAWN_COLOR[opponent_color]]) +
                (KING_WEIGHT * piece_counts[KING_COLOR[opponent_color]]))
        if my_u == 0:
            # I have no tools left
            return -INFINITY
        elif op_u == 0:
            # The opponent has no tools left
            return INFINITY
        else:
            return my_u - op_u

    def selective_deepening_criterion(self, state):
        '''in case of possible capture moves or if there is only one turn left in round
        it's worth continue deepening more than regular turn'''
        if state.calc_capture_moves():
            return True
        return False

    def no_more_time(self):
        return (time.process_time() - self.clock) >= self.time_for_current_move

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'improved')

# c:\python35\python.exe run_game.py 3 3 3 y simple_player improved_player
