from collections import defaultdict
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP, MY_COLORS, BACK_ROW, \
    RED_PLAYER, BOARD_ROWS, BOARD_COLS
from utils import INFINITY
import math

class CriteriaEval:
    criteria_num = 7

    PAWN = 3.0  # Value of pawns
    KING = 5.0  # Value of kings
    EDGE_ROWS = 2.0  # Value of piece in edge rows
    EDGE_COLS = 0.5  # Value of piece in edge columns
    CLOSE_TO_THRONE = lambda c, y: (abs((BOARD_ROWS - 1) - BACK_ROW[c] - y) - CriteriaEval.PAWN)  # Eval the pawns progress to the throne
    PROTECTED = 0.5  # Value of protected piece
    CAN_BE_TAKEN = -0.5  # Value of piece that can be taken this turn


class EvalsEnum:
    evals_num = 3

    PIECES = 0  # Index 0: Evaluation by number of pieces and type.
    LOCS = 1  # Index 1: Evaluation by piece locations on the board.
    DISTANCE = 2  # Index 2: Evaluation by the distances between the pieces.


class Evaluation:
    def __init__(self, my_color):
        self.color = my_color
        self.oppo_color = OPPONENT_COLOR[self.color]

        self.my_evals = []
        self.oppo_evals = []

    def distance(self, p1, p2):
        dx, dy = abs(p1[1] - p2[1]), abs(p1[0] - p2[0])
        return max(dx, dy)

    def calc_distances(self, piece_locs):
        m_k_num = len(piece_locs[KING_COLOR[self.color]])
        if m_k_num < 1:
            return
        sum_d = 0
        for king_loc in piece_locs[KING_COLOR[self.color]]:
            for piece_loc in piece_locs[PAWN_COLOR[self.oppo_color]] + piece_locs[KING_COLOR[self.oppo_color]]:
                sum_d += self.distance(king_loc, piece_loc) ** 2
        sum_d = math.sqrt(sum_d) if sum_d > 0 else 0
        sum_d /= (m_k_num * BOARD_ROWS)
        self.my_evals[EvalsEnum.DISTANCE] += sum_d if (m_k_num - len(
            piece_locs[KING_COLOR[self.oppo_color]])) < 0 else (1 - sum_d)

    def is_king(self, piece_val):
        # return piece_val.isupper()
        return piece_val == KING_COLOR[self.color] or piece_val == KING_COLOR[OPPONENT_COLOR[self.color]]

    def is_in_edge_rows(self, r):
        return (r == 0) or (r == (BOARD_ROWS - 1))

    def is_in_edge_cols(self, c):
        return (c == 0) or (c == (BOARD_COLS - 1))

    def is_red_player_piece(self, piece_val):
        return piece_val == PAWN_COLOR[RED_PLAYER] or piece_val == KING_COLOR[RED_PLAYER]

    # Loop over the 'pieces' and check if they all belong to same player return True, and False otherwise.
    def of_same_player(self, pieces):
        for i in range(len(pieces) - 1):
            if pieces[i].lower() != pieces[i + 1].lower():
                return False
        return True

    # Get the both diagonally locations before the given piece_loc.
    def get_loc_before(self, piece_val, piece_loc):
        r, c = 0, 1
        if self.is_red_player_piece(piece_val):
            return [(piece_loc[r] + 1, piece_loc[c] + 1), (piece_loc[r] + 1, piece_loc[c] - 1)]
        return [(piece_loc[r] - 1, piece_loc[c] - 1), (piece_loc[r] - 1, piece_loc[c] + 1)]

    # Get the both diagonally locations after the given piece_loc.
    def get_loc_after(self, piece_val, piece_loc):
        r, c = 0, 1
        if self.is_red_player_piece(piece_val):
            return [(piece_loc[r] - 1, piece_loc[c] - 1), (piece_loc[r] - 1, piece_loc[c] + 1)]
        return [(piece_loc[r] + 1, piece_loc[c] + 1), (piece_loc[r] + 1, piece_loc[c] - 1)]

    # Get the four diagonally locations around the given piece_loc.
    def get_loc_around(self, piece_val, piece_loc):
        return self.get_loc_before(piece_val, piece_loc) + self.get_loc_after(piece_val, piece_loc)

    # Checks if the piece is protected that can't be eaten.
    def is_protected(self, state, piece_val, piece_loc):
        r, c = 0, 1
        if piece_loc[r] > 0 and piece_loc[r] < BOARD_ROWS - 1 and piece_loc[c] > 0 and piece_loc[c] < BOARD_COLS - 1:
            loc_around = self.get_loc_around(piece_val, piece_loc)
            for i in range(len(loc_around)):
                if self.of_same_player([piece_val, state.board[loc_around[i]], state.board[loc_around[(i + 1) % 4]]]):
                    return True
        return False

    # checks if the piece can be eaten this turn.
    def is_can_be_taken(self, state, piece_val, piece_loc):
        loc_before = self.get_loc_before(piece_val, piece_loc)
        loc_after = self.get_loc_after(piece_val, piece_loc)

        r, c = 0, 1
        if piece_loc[r] > 0 and piece_loc[r] < BOARD_ROWS - 1 and piece_loc[c] > 0 and piece_loc[c] < BOARD_COLS - 1:
            for i in range(len(loc_before)):
                if loc_before[i] != EM and not self.of_same_player([piece_val, state.board[loc_before[i]]]):
                    if loc_after[i] == EM:
                        return True
            for i in range(len(loc_after)):
                if self.is_king(state.board[loc_after[i]]) and not self.of_same_player(
                        [piece_val, state.board[loc_after[i]]]):
                    if loc_before[i] == EM:
                        return True
        return False

    def pieces_evaluation(self, piece_locs, weights=(1.0, 1.5)):
        self.my_evals[EvalsEnum.PIECES] = (weights[0] * len(piece_locs[PAWN_COLOR[self.color]])) + (
                weights[1] * len(piece_locs[KING_COLOR[self.color]]))
        self.oppo_evals[EvalsEnum.PIECES] = (weights[0] * len(piece_locs[PAWN_COLOR[self.oppo_color]])) + (
                weights[1] * len(piece_locs[KING_COLOR[self.oppo_color]]))

    def loc_evaluation(self, state, piece_locs):
        epsilon = 0.0000001

        def iterate_eval(clr):
            eval = 0.0
            for (r, c) in piece_locs[PAWN_COLOR[clr]] + piece_locs[KING_COLOR[clr]]:
                if len(piece_locs[PAWN_COLOR[OPPONENT_COLOR[clr]]]) <= 1 and not self.is_king(state.board[(r, c)]):
                    eval += CriteriaEval.CLOSE_TO_THRONE(self.color, r)
                elif self.is_in_edge_rows(r):
                    eval += CriteriaEval.EDGE_ROWS
                elif self.is_in_edge_cols(c):
                    eval += CriteriaEval.EDGE_COLS
                if self.is_protected(state, PAWN_COLOR[self.oppo_color], (r, c)):
                    eval += CriteriaEval.PROTECTED
                elif self.is_can_be_taken(state, PAWN_COLOR[self.oppo_color], (r, c)):
                    eval += CriteriaEval.CAN_BE_TAKEN
            return eval

        my_eval = (CriteriaEval.KING * len(piece_locs[KING_COLOR[self.color]])) + (CriteriaEval.PAWN * len(piece_locs[PAWN_COLOR[self.color]])) + iterate_eval(self.color)
        oppo_eval = (CriteriaEval.KING * len(piece_locs[KING_COLOR[self.oppo_color]])) + (CriteriaEval.PAWN * len(piece_locs[PAWN_COLOR[self.oppo_color]])) + iterate_eval(self.oppo_color)
        m_p_count = len(piece_locs[PAWN_COLOR[self.color]]) + len(piece_locs[KING_COLOR[self.color]])
        o_p_count = len(piece_locs[PAWN_COLOR[self.oppo_color]]) + len(piece_locs[KING_COLOR[self.oppo_color]])
        self.my_evals[EvalsEnum.LOCS] = my_eval / (m_p_count if m_p_count else epsilon)
        self.oppo_evals[EvalsEnum.LOCS] = oppo_eval / (o_p_count if o_p_count else epsilon)

    def run_evals(self, state, weights=None):
        self.my_evals = [0] * EvalsEnum.evals_num
        self.oppo_evals = [0] * EvalsEnum.evals_num

        piece_locs = defaultdict(lambda: [])
        for loc, val in state.board.items():
            if val != EM:
                piece_locs[val].append(loc)

        self.pieces_evaluation(piece_locs, weights) if weights else self.pieces_evaluation(piece_locs)
        self.loc_evaluation(state, piece_locs)
        self.calc_distances(piece_locs)

    def utility(self, state, weights=(1.0, 1.0, 1.0)):

        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        self.run_evals(state, (100.0, 150.0))

        if self.my_evals[EvalsEnum.PIECES] == 0:
            # I have no tools left
            return -INFINITY
        elif self.oppo_evals[EvalsEnum.PIECES] == 0:
            # The opponent has no tools left
            return INFINITY
        else:
            utility = 0.0
            for i in range(len(weights)):
                utility += (weights[i] * (self.my_evals[i] - self.oppo_evals[i]))
            return utility
