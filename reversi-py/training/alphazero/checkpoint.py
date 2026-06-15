"""AlphaZero チェックポイント管理（ベストモデルのみ保存）。"""
from __future__ import annotations

from pathlib import Path

import torch

from agents.networks.othello_net import OthelloNNet


def save_best(net: OthelloNNet, path: str | Path) -> None:
    """ベストモデルを alpha_zero_agent.py と互換の形式で保存する。"""
    torch.save({"state_dict": net.state_dict()}, str(path))


def load_checkpoint(net: OthelloNNet, path: str | Path) -> None:
    """チェックポイントを net にロードする。"""
    checkpoint = torch.load(str(path), map_location="cpu")
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        net.load_state_dict(checkpoint["state_dict"])
    elif isinstance(checkpoint, dict) and "model_state" in checkpoint:
        net.load_state_dict(checkpoint["model_state"])
    else:
        net.load_state_dict(checkpoint)
