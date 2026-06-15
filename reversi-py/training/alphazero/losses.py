"""AlphaZero 損失関数（policy soft-target CE + value MSE）。"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def alphazero_loss(
    logits: torch.Tensor,
    value_pred: torch.Tensor,
    pi_target: torch.Tensor,
    z_target: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """policy（soft-target CE）+ value（MSE）の合計損失を計算する。

    Args:
        logits: (batch, action_size) のロジット（softmax 前）。
        value_pred: (batch, 1) の価値予測（tanh [-1, 1]）。
        pi_target: (batch, action_size) の MCTS 訪問数分布（合計 1）。
        z_target: (batch,) の終局結果（手番視点で +1/-1/0）。

    Returns:
        (total_loss, policy_loss, value_loss) のタプル。
    """
    log_probs = F.log_softmax(logits, dim=1)
    policy_loss = -(pi_target * log_probs).sum(dim=1).mean()
    value_loss = F.mse_loss(value_pred.squeeze(1), z_target)
    return policy_loss + value_loss, policy_loss, value_loss
