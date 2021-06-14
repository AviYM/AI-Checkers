from collections import defaultdict
import math
from utils import INFINITY
from checkers.consts import EM, PAWN_COLOR, KING_COLOR, OPPONENT_COLOR, MAX_TURNS_NO_JUMP, BOARD_ROWS, BOARD_COLS, \
    RED_PLAYER, MY_COLORS, BACK_ROW


class CriteriaEnum:
    criteria_num = 8

    PAWN_NUM = 0  # Index 0: Number of pawns
    KING_NUM = 1  # Index 1: Number of kings
    EDGE_ROWS = 2  # Index 2: Number in edge rows
    EDGE_COLS = 3  # Index 3: Number in edge columns
    PROTECTED = 4  # Index 4: Number that are protected
    CLOSE_TO_THRONE = 5  # Index 5: count the pawns progress to the throne
    CAN_BE_TAKEN = 6  # Index 6: Number that can be taken this turn
    DISTANCE = 7  # Index 7: The average distance between the kings and all my other pieces.


class Evaluation:
    def __init__(self, my_color):
        self.color = my_color

        self.my_criteria = []
        self.oppo_criteria = []
        return

    # Calculate the Chebyshev distance of two points.
    def distance(self, p1, p2):
        dx, dy = abs(p1[1] - p2[1]), abs(p1[0] - p2[0])
        return max(dx, dy)

    def calc_distances(self, piece_locs):
        m_k_num = len(piece_locs[KING_COLOR[self.color]])
        if m_k_num < 1:
            return
        sum_d = 0
        for king_loc in piece_locs[KING_COLOR[self.color]]:
            for piece_loc in piece_locs[PAWN_COLOR[self.color]] + piece_locs[KING_COLOR[self.color]]:
                sum_d += self.distance(king_loc, piece_loc) ** 2
        sum_d = math.sqrt(sum_d) if sum_d > 0 else 0
        sum_d /= (m_k_num * BOARD_ROWS)
        self.my_criteria[CriteriaEnum.DISTANCE] = sum_d if (m_k_num - len(
            piece_locs[KING_COLOR[OPPONENT_COLOR[self.color]]])) < 0 else (1 - sum_d)

    # Returns True if the given piece_val is a king and False otherwise.
    def is_king(self, piece_val):
        # return piece_val.isupper()
        return piece_val == KING_COLOR[self.color] or piece_val == KING_COLOR[OPPONENT_COLOR[self.color]]

    # Given a 'piece', return true if it belongs to a 'self.color' player.
    def is_my_piece(self, piece):
        return piece in MY_COLORS[self.color]

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

    def loc_evaluation(self, weights):
        my_eval, oppo_eval, epsilon = 0, 0, 0.0000001

        m_p_num = self.my_criteria[CriteriaEnum.PAWN_NUM]
        my_eval += (weights[CriteriaEnum.KING_NUM] * self.my_criteria[CriteriaEnum.KING_NUM])
        my_eval += (weights[CriteriaEnum.CLOSE_TO_THRONE] * self.my_criteria[CriteriaEnum.CLOSE_TO_THRONE])
        m_p_num -= self.my_criteria[CriteriaEnum.CLOSE_TO_THRONE]
        my_eval += (weights[CriteriaEnum.EDGE_ROWS] * self.my_criteria[CriteriaEnum.EDGE_ROWS])
        m_p_num -= self.my_criteria[CriteriaEnum.EDGE_ROWS]
        my_eval += (weights[CriteriaEnum.EDGE_COLS] * self.my_criteria[CriteriaEnum.EDGE_COLS])
        m_p_num -= self.my_criteria[CriteriaEnum.EDGE_COLS]
        my_eval += (weights[CriteriaEnum.PROTECTED] * self.my_criteria[CriteriaEnum.PROTECTED])
        m_p_num -= self.my_criteria[CriteriaEnum.PROTECTED]
        my_eval += (weights[CriteriaEnum.CAN_BE_TAKEN] * self.my_criteria[CriteriaEnum.CAN_BE_TAKEN])
        m_p_num -= self.my_criteria[CriteriaEnum.CAN_BE_TAKEN]
        my_eval += (weights[CriteriaEnum.PAWN_NUM] * m_p_num)
        m_p_count = self.my_criteria[CriteriaEnum.PAWN_NUM] + self.my_criteria[CriteriaEnum.KING_NUM]
        my_eval /= m_p_count if m_p_count else epsilon

        o_p_num = self.oppo_criteria[CriteriaEnum.PAWN_NUM]
        oppo_eval += (weights[CriteriaEnum.KING_NUM] * self.oppo_criteria[CriteriaEnum.KING_NUM])
        oppo_eval += (weights[CriteriaEnum.CLOSE_TO_THRONE] * self.oppo_criteria[CriteriaEnum.CLOSE_TO_THRONE])
        o_p_num -= self.oppo_criteria[CriteriaEnum.CLOSE_TO_THRONE]
        oppo_eval += (weights[CriteriaEnum.EDGE_ROWS] * self.oppo_criteria[CriteriaEnum.EDGE_ROWS])
        o_p_num -= self.oppo_criteria[CriteriaEnum.EDGE_ROWS]
        oppo_eval += (weights[CriteriaEnum.EDGE_COLS] * self.oppo_criteria[CriteriaEnum.EDGE_COLS])
        o_p_num -= self.oppo_criteria[CriteriaEnum.EDGE_COLS]
        oppo_eval += (weights[CriteriaEnum.PROTECTED] * self.oppo_criteria[CriteriaEnum.PROTECTED])
        o_p_num -= self.oppo_criteria[CriteriaEnum.PROTECTED]
        oppo_eval += (weights[CriteriaEnum.CAN_BE_TAKEN] * self.oppo_criteria[CriteriaEnum.CAN_BE_TAKEN])
        o_p_num -= self.oppo_criteria[CriteriaEnum.CAN_BE_TAKEN]
        oppo_eval += (weights[CriteriaEnum.PAWN_NUM] * m_p_num)
        o_p_count = self.oppo_criteria[CriteriaEnum.PAWN_NUM] + self.oppo_criteria[CriteriaEnum.KING_NUM]
        oppo_eval /= o_p_count if o_p_count else epsilon

        return my_eval - oppo_eval

    # Increasing the relevant counter according to the color and the type of the given piece.
    def increase_pieces_counter(self, piece_locs):
        opponent_color = OPPONENT_COLOR[self.color]

        self.my_criteria[CriteriaEnum.PAWN_NUM] += len(piece_locs[PAWN_COLOR[self.color]])
        self.my_criteria[CriteriaEnum.KING_NUM] += len(piece_locs[KING_COLOR[self.color]])
        self.oppo_criteria[CriteriaEnum.PAWN_NUM] += len(piece_locs[PAWN_COLOR[opponent_color]])
        self.oppo_criteria[CriteriaEnum.KING_NUM] += len(piece_locs[KING_COLOR[opponent_color]])

    # Increasing the relevant back_row counter according to the color of the given piece.
    def increase_edge_counters(self, piece_locs):
        opponent_color = OPPONENT_COLOR[self.color]

        r, c = 0, 1
        for loc in piece_locs[PAWN_COLOR[self.color]]:
            if loc[r] == 0 or loc[r] == BOARD_ROWS - 1:
                self.my_criteria[CriteriaEnum.EDGE_ROWS] += 1
            elif loc[c] == 0 or loc[c] == BOARD_COLS - 1:
                self.my_criteria[CriteriaEnum.EDGE_COLS] += 1
        for loc in piece_locs[PAWN_COLOR[opponent_color]]:
            if loc[r] == 0 or loc[r] == BOARD_ROWS - 1:
                self.oppo_criteria[CriteriaEnum.EDGE_ROWS] += 1
            elif loc[c] == 0 or loc[c] == BOARD_COLS - 1:
                self.oppo_criteria[CriteriaEnum.EDGE_COLS] += 1

    # Increasing the relevant protected counter according to the color of the given piece.
    def increase_protected_counter(self, piece_val):
        if self.is_my_piece(piece_val):
            self.my_criteria[CriteriaEnum.PROTECTED] += 1
        else:  # is oppo piece.
            self.oppo_criteria[CriteriaEnum.PROTECTED] += 1

    def increase_can_be_taken_counter(self, piece_val):
        if self.is_my_piece(piece_val):
            self.my_criteria[CriteriaEnum.CAN_BE_TAKEN] += 1
        else:  # is oppo piece
            self.oppo_criteria[CriteriaEnum.CAN_BE_TAKEN] += 1

    def increase_close_to_throne_counter(self, piece_locs):
        opponent_color = OPPONENT_COLOR[self.color]

        r = 0
        self.my_criteria[CriteriaEnum.CLOSE_TO_THRONE] += sum(
            [abs((BOARD_ROWS - 1) - BACK_ROW[self.color] - loc[r]) for loc in piece_locs[PAWN_COLOR[self.color]] if
             len(piece_locs[PAWN_COLOR[opponent_color]]) <= 1])
        self.oppo_criteria[CriteriaEnum.CLOSE_TO_THRONE] += sum(
            [abs((BOARD_ROWS - 1) - BACK_ROW[opponent_color] - loc[r]) for loc in piece_locs[PAWN_COLOR[opponent_color]]
             if len(piece_locs[PAWN_COLOR[self.color]]) <= 1])

    def get_criteria(self, state):
        self.my_criteria = [0] * CriteriaEnum.criteria_num
        self.oppo_criteria = [0] * CriteriaEnum.criteria_num
        # opponent_color = OPPONENT_COLOR[self.color]

        piece_locs = defaultdict(lambda: [])
        for loc, val in state.board.items():
            if val != EM:
                piece_locs[val].append(loc)

                if self.is_protected(state, val, loc):
                    self.increase_protected_counter(val)
                elif self.is_can_be_taken(state, val, loc):
                    self.increase_can_be_taken_counter(val)

        if self.my_criteria[CriteriaEnum.CAN_BE_TAKEN] < 2:
            self.my_criteria[CriteriaEnum.CAN_BE_TAKEN] = 0
        if self.oppo_criteria[CriteriaEnum.CAN_BE_TAKEN] < 2:
            self.oppo_criteria[CriteriaEnum.CAN_BE_TAKEN] = 0

        self.increase_pieces_counter(piece_locs)
        self.increase_edge_counters(piece_locs)
        self.increase_close_to_throne_counter(piece_locs)
        self.calc_distances(piece_locs)

    def utility(self, state, weights=(100.0, 150.0, 1.0, 1.0), loc_eval_weights=(15.0, 30.0, 5.0, 3.0, 3.0, 1.0, -10.0)):

        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        self.get_criteria(state)
        eval = self.loc_evaluation(loc_eval_weights)
        utility = eval * weights[3]
        utility += (weights[2] * self.my_criteria[CriteriaEnum.DISTANCE])

        if self.my_criteria[CriteriaEnum.PAWN_NUM] + self.my_criteria[CriteriaEnum.KING_NUM] == 0:
            # I have no tools left
            return -INFINITY
        elif self.oppo_criteria[CriteriaEnum.PAWN_NUM] + self.oppo_criteria[CriteriaEnum.KING_NUM] == 0:
            # The opponent has no tools left
            return INFINITY
        else:
            for i in range(len(weights) - 1):
                utility += (weights[i] * (self.my_criteria[i] - self.oppo_criteria[i]))
            return utility

