# ===============================================================================
# Imports
# ===============================================================================

import players.simple_player as simple_player
from ..evaluation import Evaluation

# ===============================================================================
# Player
# ===============================================================================

class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        simple_player.Player.__init__(self, setup_time, player_color, time_per_k_turns, k)

    def utility(self, state):
        eval = Evaluation(self.color)
        return eval.utility(state)
