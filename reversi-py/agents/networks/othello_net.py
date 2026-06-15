"""alpha-zero-general の OthelloNNet アーキテクチャをポート"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class OthelloNNet(nn.Module):
    """Othello/Reversi 用 CNN（alpha-zero-general から移植）"""

    def __init__(self, board_size: int = 8, dropout: float = 0.3) -> None:
        super().__init__()
        self.board_size = board_size
        self.action_size = board_size * board_size + 1  # +1 はパス

        # 畳み込み層
        self.conv1 = nn.Conv2d(1, 128, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(128)
        self.conv2 = nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.conv3 = nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=0)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=0)
        self.bn4 = nn.BatchNorm2d(128)

        # 全結合層
        self.fc1 = nn.Linear(128 * (board_size - 4) * (board_size - 4), 512)
        self.fc_bn1 = nn.BatchNorm1d(512)
        self.fc2 = nn.Linear(512, 256)
        self.fc_bn2 = nn.BatchNorm1d(256)

        # 出力層
        self.fc_pi = nn.Linear(256, self.action_size)  # 方策
        self.fc_v = nn.Linear(256, 1)  # 価値

        self.dropout = dropout

    def forward(self, board: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            board: (batch, 8, 8) or (batch, 1, 8, 8)
        Returns:
            (pi, v): (batch, 65) 方策と (batch, 1) 価値
        """
        # board が (batch, 8, 8) なら (batch, 1, 8, 8) に変換
        if board.dim() == 3:
            board = board.unsqueeze(1)

        # 畳み込み処理
        x = F.relu(self.bn1(self.conv1(board)))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.bn3(self.conv3(x)))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.bn4(self.conv4(x)))
        x = F.dropout(x, p=self.dropout, training=self.training)

        # フラット化
        x = x.reshape(x.size(0), -1)

        # 全結合層
        x = F.relu(self.fc_bn1(self.fc1(x)))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.fc_bn2(self.fc2(x)))
        x = F.dropout(x, p=self.dropout, training=self.training)

        # 出力層
        pi = self.fc_pi(x)  # ロジット
        v = torch.tanh(self.fc_v(x))  # -1 から 1

        return pi, v
