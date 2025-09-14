import os
from typing import Optional

from ai.minimax import minimax
from backend.board import GameState
from utils.messages import add_message

try:
    import tensorflow as tf

    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False


class DNNAgent:
    def __init__(
        self, model_path: Optional[str] = "dnn_eval.h5", depth_fallback: int = 2
    ):
        self.model_path = model_path
        self.model = None
        self.depth_fallback = depth_fallback
        if TF_AVAILABLE and os.path.exists(self.model_path):
            try:
                self.model = tf.keras.models.load_model(self.model_path)
            except Exception as e:
                add_message(f"Failed to load DNN model: {e}")
                self.model = None

    def take_turn(self, gs: GameState) -> None:
        if self.model is None:
            # fallback to minimax
            sc, action = minimax(
                gs,
                depth=self.depth_fallback,
                alpha=-(10**9),
                beta=10**9,
                maximizing=True,
                team=2,
            )
            if action and action.get("type") == "attack":
                # try to find unit and target in real gs and apply
                from core.logic import apply_attack, move_unit

                attacker = action["unit"]
                target = action["target"]
                # best-effort: find matching units by proximity
                real_att = None
                real_t = None
                for u in gs.units:
                    if u.name == attacker.name and u.team == attacker.team:
                        real_att = u
                        break
                for u in gs.units:
                    if u.name == target.name and u.team == target.team:
                        real_t = u
                        break
                if real_att and real_t:
                    apply_attack(real_att, real_t, gs)
            elif action and action.get("type") == "move":
                from core.logic import move_unit

                attacker = action["unit"]
                to = action["to"]
                real_att = None
                for u in gs.units:
                    if u.name == attacker.name and u.team == attacker.team:
                        real_att = u
                        break
                if real_att:
                    move_unit(real_att, gs, to[0], to[1])
            return
        # if model exists: produce state vector and predict (left as extension)
        add_message(
            "DNNAgent: model present but prediction pipeline not "
            "implemented; fallback used."
        )

        # fallback to minimax:
        self.take_turn(gs)
