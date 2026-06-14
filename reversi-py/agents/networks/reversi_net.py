"""リバーシ用 ResNet（Policy + Value head）。

入力: (batch, 2, 8, 8) の盤面表現
出力: (policy logits, value)
"""
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    raise ImportError("PyTorch is required for AlphaZeroAgent. Install with: uv sync --extra ml")


class ResBlock(nn.Module):
    """残差ブロック（Conv → BN → ReLU → Conv → BN + skip）。"""

    def __init__(self, n_filters: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(n_filters, n_filters, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(n_filters)
        self.conv2 = nn.Conv2d(n_filters, n_filters, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(n_filters)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """順伝播。"""
        residual = x
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = self.bn2(x)
        x = x + residual
        x = F.relu(x)
        return x


class ReversiNet(nn.Module):
    """リバーシ用 ResNet。

    Args:
        board_size: 盤面サイズ（デフォルト 8）。
        n_res_blocks: 残差ブロック数。
        n_filters: 特徴マップ数。
    """

    def __init__(
        self,
        board_size: int = 8,
        n_res_blocks: int = 4,
        n_filters: int = 64,
    ) -> None:
        super().__init__()
        self.board_size = board_size
        self.n_filters = n_filters

        # 入力層
        self.conv_in = nn.Conv2d(2, n_filters, 3, padding=1)
        self.bn_in = nn.BatchNorm2d(n_filters)

        # 残差ブロック
        self.res_blocks = nn.ModuleList([
            ResBlock(n_filters) for _ in range(n_res_blocks)
        ])

        # Policy head
        self.policy_conv = nn.Conv2d(n_filters, 2, 1)
        self.policy_bn = nn.BatchNorm2d(2)
        policy_fc_input = 2 * board_size * board_size
        self.policy_fc = nn.Linear(policy_fc_input, board_size * board_size + 1)

        # Value head
        self.value_conv = nn.Conv2d(n_filters, 1, 1)
        self.value_bn = nn.BatchNorm2d(1)
        value_fc_input = board_size * board_size
        self.value_fc1 = nn.Linear(value_fc_input, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """順伝播。

        Args:
            x: (batch, 2, board_size, board_size) の入力テンソル。

        Returns:
            (policy_logits, value) のタプル。
            policy_logits: (batch, board_size^2 + 1)
            value: (batch, 1)
        """
        # 共通部分
        x = self.conv_in(x)
        x = self.bn_in(x)
        x = F.relu(x)

        for res_block in self.res_blocks:
            x = res_block(x)

        # Policy head
        policy = self.policy_conv(x)
        policy = self.policy_bn(policy)
        policy = F.relu(policy)
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)

        # Value head
        value = self.value_conv(x)
        value = self.value_bn(value)
        value = F.relu(value)
        value = value.view(value.size(0), -1)
        value = self.value_fc1(value)
        value = F.relu(value)
        value = torch.tanh(self.value_fc2(value))

        return policy, value
