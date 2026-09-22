"""Train a PPO policy for the Kaggriculture farmer's tile-tending action
(see env.py's module docstring for what is and isn't RL-controlled).

Usage:
    python training/train.py --timesteps 300000 --opponent starter --out training/models/ppo_farmer
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CallbackList, CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv

from env import KaggricultureFarmerEnv


class ProgressCallback(BaseCallback):
    """Print periodic training progress: timesteps, episodes, and a
    rolling average of final money from completed episodes."""

    def __init__(self, print_every: int = 5000):
        super().__init__()
        self.print_every = print_every
        self._last_print = 0
        self._recent_money: list[float] = []
        self._start_time = time.time()

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "final_money" in info:
                self._recent_money.append(info["final_money"])
                self._recent_money = self._recent_money[-50:]
        if self.num_timesteps - self._last_print >= self.print_every:
            self._last_print = self.num_timesteps
            elapsed = time.time() - self._start_time
            avg_money = sum(self._recent_money) / len(self._recent_money) if self._recent_money else float("nan")
            print(
                f"[{elapsed:7.1f}s] timesteps={self.num_timesteps:>8} "
                f"episodes_seen={len(self._recent_money):>3} (rolling window) "
                f"avg_final_money(last<=50)={avg_money:9.1f}",
                flush=True,
            )
        return True


def make_env(opponent: str, episode_steps: int):
    def _init():
        return KaggricultureFarmerEnv(opponent=opponent, episode_steps=episode_steps)

    return _init


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=300_000)
    parser.add_argument("--opponent", default="starter", help="Built-in name (pass/random/starter) or a path to a bundled submission (e.g. submissions/v7/main.py) for self-play")
    parser.add_argument("--episode-steps", type=int, default=192, help="Shorter than the real 720 for faster training throughput")
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--out", default="training/models/ppo_farmer")
    parser.add_argument("--print-every", type=int, default=5000)
    parser.add_argument("--checkpoint-every", type=int, default=100_000, help="Save an intermediate checkpoint every N timesteps, so progress can be evaluated without waiting for the full run")
    args = parser.parse_args()

    vec_env = DummyVecEnv([make_env(args.opponent, args.episode_steps) for _ in range(args.n_envs)])

    model = PPO(
        "MlpPolicy",
        vec_env,
        verbose=0,
        n_steps=512,
        batch_size=256,
        learning_rate=3e-4,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_cb = CheckpointCallback(
        save_freq=max(1, args.checkpoint_every // args.n_envs),
        save_path=str(out_path.parent / "checkpoints"),
        name_prefix=out_path.name,
    )

    print(f"Training PPO for {args.timesteps} timesteps vs '{args.opponent}' ({args.episode_steps}-step episodes, {args.n_envs} parallel envs)...", flush=True)
    model.learn(
        total_timesteps=args.timesteps,
        callback=CallbackList([ProgressCallback(args.print_every), checkpoint_cb]),
    )

    model.save(str(out_path))
    print(f"Saved model to {out_path}.zip", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
