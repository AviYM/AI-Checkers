import csv

import run_game
from checkers.consts import RED_PLAYER, BLACK_PLAYER

SETUP_TIME = 2
K_ROUNDS = 5
IS_VERBOSE = 'n'
LOSE_SCORE = 0
TIE_SCORE = 0.5
WIN_SCORE = 1


def run_all_tests(test_times, players_kind, results_file_name):
    """
    run all tests according to the given params and write into a file
    :param test_times: list of times to run the game [2,10,50]
    :param players_kind: list of different kind of players (simple, better etc..)
    :param results_file_name: the name of the file to write results to
    :return: void
    """
    test_number = 0
    test_results = []

    for time in test_times:
        for p1 in players_kind:
            for p2 in players_kind:
                # avoid game with the same kind of players
                if p1 == p2:
                    continue

                test_number += 1
                print("test " + str(
                    test_number) + ") => player 1: " + p1 + ". player 2: " + p2 + ". time: " + str(time))

                single_test_result = run_single_test(time, p1, p2)
                print(single_test_result)
                test_results.append(single_test_result)

    write_results_to_csv_file(test_results, results_file_name)


def run_single_test(round_time, p1, p2):
    """run a single test according to params
    :param round_time: time for each k_rounds
    :param p1: the kind of player 1
    :param p2: the kind of player 2
    :return: list representing the test result [player1, player2, round_time, player1_score, player2_score]
    """
    # args: setup_time = 2, round_time = var, k_rounds = 5, is_verbose = no, player1 = var, player2 = var
    args = [SETUP_TIME, round_time, K_ROUNDS, IS_VERBOSE, p1, p2]
    test_result = [p1, p2, round_time]

    game_result = run_game.GameRunner(*args).run()
    score = get_game_score(game_result)
    test_result.extend(score)
    return test_result


def get_game_score(game_result):
    """
    get the scores for both players according to game result
    :param game_result: the result of the game. tie, red player or black player
    :return: list of scores for both players [tie,tie] or [win,lose] or [lose, win]
    """
    if game_result == run_game.TIE:
        return [TIE_SCORE, TIE_SCORE]
    elif game_result[0] == RED_PLAYER:
        return [WIN_SCORE, LOSE_SCORE]
    else:
        return [LOSE_SCORE, WIN_SCORE]


def write_results_to_csv_file(results, file_name):
    """
    write all tests results to csv file
    :param results: list of results from each test
    :param file_name: csv file to write into
    :return: void
    """
    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for result in results:
            writer.writerow(result)


if __name__ == '__main__':
    test_times = ['2','10','50']
    players_kind = ['simple_player', 'better_h_player', 'improved_player', 'improved_better_h_player']
    file_name = 'experiments.csv'
    run_all_tests(test_times, players_kind, file_name)
