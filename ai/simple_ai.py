from base_agent import BaseAgent

from backend.board import GameState
from backend.logic import apply_attack, move_unit
from utils.helpers import distance


class SimpleAgent(BaseAgent):
    def take_turn(self, gs: GameState) -> None:
        ai_units = [u for u in gs.units if u.team == 2 and u.hp > 0]
        enemies = [u for u in gs.units if u.team == 1 and u.hp > 0]
        if not enemies:
            return
        for u in ai_units:
            # attack if someone in range
            target = min(enemies, key=lambda e: distance(u.x, u.y, e.x, e.y))
            if distance(u.x, u.y, target.x, target.y) <= max(1, u.stats.range):
                apply_attack(u, target, gs)
                continue
            # else try to step closer in 4-neighborhood (greedy)
            best = None
            best_d = 10**9
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx, ty = u.x + dx, u.y + dy
                if not gs.in_bounds(tx, ty):
                    continue
                if gs.get_unit_at(tx, ty) is not None:
                    continue
                d = distance(tx, ty, target.x, target.y)
                if d < best_d:
                    best_d = d
                    best = (tx, ty)
            if best:
                move_unit(u, gs, best[0], best[1])
