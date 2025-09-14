"""
def evaluate_state(gs: GameState) -> int:
    # egyszerű: összeadjuk a csapat health különbségét + pozíciós bónusz (domb)
    score = 0
    for u in gs.units:
        val = u.health
        # small positional bonus: prefer hill
        if gs.tile(u.x, u.y).name == "HILL":
            val += 1
        score += val if u.team == 1 else -val
    return score


def clone_state(gs: GameState) -> GameState:
    return copy.deepcopy(gs)


def generate_actions_for_team(gs: GameState, team: int):
    actions = []
    units = [u for u in gs.units if u.team == team and u.health > 0 and not u.has_acted]
    if not units:
        return [{"type": "noop"}]
    u = units[0]  # simplify: only expand the first unit to reduce branching
    # attack actions
    for target in gs.units:
        if target.team != u.team and target.health > 0:
            if distance(u.x, u.y, target.x, target.y) <= max(1, u.stats.range):
                actions.append({"type": "attack", "unit": u, "target": target})
    # move actions: 4-neighborhood
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tx, ty = u.x + dx, u.y + dy
        if (
            gs.in_bounds(tx, ty)
            and gs.get_unit_at(tx, ty) is None
            and gs.tile(tx, ty).name != "MOUNTAIN"
        ):
            actions.append({"type": "move", "unit": u, "to": (tx, ty)})
    if not actions:
        actions.append({"type": "pass", "unit": u})
    return actions


def apply_action_on_clone(gs: GameState, action) -> GameState:
    ngs = clone_state(gs)
    # find corresponding unit by identity (positions and names)
    if action["type"] == "noop":
        return ngs

    # find unit in ngs matching action unit original pos & name
    def find_unit(orig):
        for uu in ngs.units:
            if (
                uu.name == orig.name
                and uu.x == orig.x
                and uu.y == orig.y
                and uu.team == orig.team
            ):
                return uu
        # fallback: find any same team alive
        for uu in ngs.units:
            if uu.team == orig.team and uu.health > 0:
                return uu
        return None

    if action["type"] in ("attack", "move", "pass"):
        orig_unit = action["unit"]
        u = find_unit(orig_unit)
        if u is None:
            return ngs
        if action["type"] == "move":
            tx, ty = action["to"]
            move_unit(u, ngs, tx, ty)
        elif action["type"] == "attack":
            orig_target = action["target"]
            t = find_unit(orig_target)
            if t:
                apply_attack(u, t, ngs)
        # pass does nothing
    return ngs


def minimax(
    gs: GameState, depth: int, alpha: int, beta: int, maximizing: bool, team: int
) -> Tuple[int, Optional[dict]]:
    teams = {u.team for u in gs.units if u.health > 0}
    if (1 in teams) and (2 not in teams):
        return 10**6, None
    if (2 in teams) and (1 not in teams):
        return -(10**6), None

    if depth == 0:
        return evaluate_state(gs), None

    actions = generate_actions_for_team(
        gs, team if maximizing else (1 if team == 2 else 2)
    )
    best_action = None
    if maximizing:
        value = -(10**9)
        for a in actions:
            ngs = apply_action_on_clone(gs, a)
            # after action, mark unit acted -> simulate end-of-turn when all acted
            sc, _ = minimax(ngs, depth - 1, alpha, beta, False, team)
            if sc > value:
                value = sc
                best_action = a
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_action
    else:
        value = 10**9
        for a in actions:
            ngs = apply_action_on_clone(gs, a)
            sc, _ = minimax(ngs, depth - 1, alpha, beta, True, team)
            if sc < value:
                value = sc
                best_action = a
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_action
"""
