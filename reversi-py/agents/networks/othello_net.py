"""alpha-zero-general の OthelloNNet アーキテクチャをポート"""
import torch
import torch.nn as nn
import torch.nn.functional as F

# alpha-zero-general OthelloNNet のハイパーパラメータ
# 値・レイヤ名・形状は学習済みモデル（alpha_zero_8x8_best.pth.tar）と一致させること
_NUM_CHANNELS: int = 512
_FC1_UNITS: int = 1024
_FC2_UNITS: int = 512
_DEFAULT_DROPOUT: float = 0.3


class OthelloNNet(nn.Module):
    """Othello/Reversi 用 CNN（alpha-zero-general から移植）"""

    def __init__(self, board_size: int = 8, dropout: float = _DEFAULT_DROPOUT) -> None:
        super().__init__()
        self.board_size = board_size
        self.action_size = board_size * board_size + 1  # +1 はパス

        # 畳み込み層（alpha-zero-general の OthelloNNet アーキテクチャ）
        self.conv1 = nn.Conv2d(1, _NUM_CHANNELS, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(_NUM_CHANNELS)
        self.conv2 = nn.Conv2d(_NUM_CHANNELS, _NUM_CHANNELS, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(_NUM_CHANNELS)
        self.conv3 = nn.Conv2d(_NUM_CHANNELS, _NUM_CHANNELS, kernel_size=3, stride=1, padding=0)
        self.bn3 = nn.BatchNorm2d(_NUM_CHANNELS)
        self.conv4 = nn.Conv2d(_NUM_CHANNELS, _NUM_CHANNELS, kernel_size=3, stride=1, padding=0)
        self.bn4 = nn.BatchNorm2d(_NUM_CHANNELS)

        # 全結合層
        self.fc1 = nn.Linear(_NUM_CHANNELS * (board_size - 4) * (board_size - 4), _FC1_UNITS)
        self.fc_bn1 = nn.BatchNorm1d(_FC1_UNITS)
        self.fc2 = nn.Linear(_FC1_UNITS, _FC2_UNITS)
        self.fc_bn2 = nn.BatchNorm1d(_FC2_UNITS)

        # 出力層
        self.fc3 = nn.Linear(_FC2_UNITS, self.action_size)  # 方策
        self.fc4 = nn.Linear(_FC2_UNITS, 1)  # 価値

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
        pi = self.fc3(x)  # ロジット
        v = torch.tanh(self.fc4(x))  # -1 から 1

        return pi, v
