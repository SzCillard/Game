# ai/minimax.py
"""
Minimax algorithm with alpha-beta pruning
and game state evalutuation by NEAT network.
"""


def minimax(game, depth, alpha, beta, evaluator, is_maximizing):
    if depth == 0 or game.is_terminal():
        return evaluator.evaluate_state(game.get_state_snapshot())

    moves = game.get_legal_moves()
    if is_maximizing:
        value = -1e9
        for move in moves:
            # TODO: legal moves api call, building the legal move tree
            next_state = game.simulate_move(move)
            value = max(
                value, minimax(next_state, depth - 1, alpha, beta, evaluator, False)
            )
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 1e9
        for move in moves:
            next_state = game.simulate_move(move)
            value = min(
                value, minimax(next_state, depth - 1, alpha, beta, evaluator, True)
            )
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
