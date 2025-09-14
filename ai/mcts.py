"""
import copy
import random
from backend.board import GameState
from backend.rules import apply_attack, move_unit, manhattan


class MCTSAgent:
    def __init__(self, iterations: int = 100):
        self.iterations = iterations

    def take_turn(self, gs: GameState) -> None:
        # Very simple: run rollouts from available primitive actions
        # and pick the best average reward
        ai_units = [u for u in gs.units if u.team == 2 and u.hp > 0]
        enemies = [u for u in gs.units if u.team == 1 and u.hp > 0]
        if not enemies:
            return

        candidate_actions = []
        for u in ai_units:
            # Attack candidates
            for e in enemies:
                if manhattan(u.x, u.y, e.x, e.y) <= max(1, u.stats.range):
                    candidate_actions.append(("attack", u, e))
            # Moves
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx, ty = u.x + dx, u.y + dy
                if (
                    gs.in_bounds(tx, ty)
                    and gs.get_unit_at(tx, ty) is None
                    and gs.tile(tx, ty).name != "MOUNTAIN"
                ):
                    candidate_actions.append(("move", u, (tx, ty)))

        if not candidate_actions:
            return

        scores = {a: 0.0 for a in candidate_actions}
        for a in candidate_actions:
            total = 0.0
            for _ in range(self.iterations):
                total += self.simulate(gs, a)
            scores[a] = total / self.iterations

        best = max(scores.items(), key=lambda kv: kv[1])[0]

        # Apply best action for real
        kind = best[0]
        if kind == "attack":
            apply_attack(best[1], best[2], gs)
        else:
            move_unit(best[1], gs, best[2][0], best[2][1])

    def simulate(self, gs: GameState, action) -> float:
        sim = copy.deepcopy(gs)
        kind = action[0]

        if kind == "attack":
            # Find matching units in sim
            u = self.find_matching_unit(sim, action[1])
            t = self.find_matching_unit(sim, action[2])
            if u and t:
                apply_attack(u, t, sim)
        else:
            u = self.find_matching_unit(sim, action[1])
            if u:
                move_unit(u, sim, action[2][0], action[2][1])

        # Random rollout: play a few random moves (small depth)
        for _ in range(6):
            all_units = [u for u in sim.units if u.hp > 0]
            if not any(u.team == 1 for u in all_units) or not any(
                u.team == 2 for u in all_units
            ):
                break

            # Choose random unit and random legal action (move or attack)
            u = random.choice(all_units)

            # Try attack if possible
            enemies = [e for e in all_units if e.team != u.team]
            attacked = False
            for e in enemies:
                if manhattan(u.x, u.y, e.x, e.y) <= max(1, u.stats.range):
                    apply_attack(u, e, sim)
                    attacked = True
                    break
            if attacked:
                continue

            # Else random move
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                tx, ty = u.x + dx, u.y + dy
                if (
                    sim.in_bounds(tx, ty)
                    and sim.get_unit_at(tx, ty) is None
                    and sim.tile(tx, ty).name != "MOUNTAIN"
                ):
                    move_unit(u, sim, tx, ty)
                    break

        # Evaluation: positive if AI has advantage
        score = 0
        for u in sim.units:
            score += u.hp if u.team == 2 else -u.hp
        return score

    def find_matching_unit(self, sim: GameState, orig):
        for u in sim.units:
            if (
                u.name == orig.name
                and u.team == orig.team
                and (abs(u.x - orig.x) + abs(u.y - orig.y)) <= 2
            ):
                return u
        # Best effort
        for u in sim.units:
            if u.team == orig.team and u.hp > 0:
                return u
        return None
"""
