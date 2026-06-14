"""Edax 式パターン評価（8x8 盤面用）。

エッジパターン、コーナーパターン、対角線パターンを使用した評価関数。
"""
import json
import numpy as np
from typing import Optional
from pathlib import Path


class PatternEvaluator:
    """パターンベースの評価関数。

    Args:
        board_size: 盤面サイズ（デフォルト 8）。
        weights_path: 学習済み重みファイルのパス（オプション）。
    """

    def __init__(
        self,
        board_size: int = 8,
        weights_path: Optional[str] = None,
    ) -> None:
        self.board_size = board_size

        # パターン定義（マスのインデックスリスト）
        if board_size == 8:
            # エッジパターン（各辺の 8 マス）
            self.top_edge_squares = [(0, i) for i in range(8)]
            self.bottom_edge_squares = [(7, i) for i in range(8)]
            self.left_edge_squares = [(i, 0) for i in range(8)]
            self.right_edge_squares = [(i, 7) for i in range(8)]

            # コーナー X パターン（角周辺 2x4）
            self.corner_tl = [(0, 0), (0, 1), (1, 0), (1, 1),
                              (0, 2), (0, 3), (1, 2), (1, 3)]
            self.corner_tr = [(0, 7), (0, 6), (1, 7), (1, 6),
                              (0, 5), (0, 4), (1, 5), (1, 4)]
            self.corner_bl = [(7, 0), (7, 1), (6, 0), (6, 1),
                              (7, 2), (7, 3), (6, 2), (6, 3)]
            self.corner_br = [(7, 7), (7, 6), (6, 7), (6, 6),
                              (7, 5), (7, 4), (6, 5), (6, 4)]

            # 対角線パターン
            self.diag8 = [(i, i) for i in range(8)]
            self.diag7_tl = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
            self.diag7_bl = [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6)]

            self.patterns = {
                'top_edge': self.top_edge_squares,
                'bottom_edge': self.bottom_edge_squares,
                'left_edge': self.left_edge_squares,
                'right_edge': self.right_edge_squares,
                'corner_tl': self.corner_tl,
                'corner_tr': self.corner_tr,
                'corner_bl': self.corner_bl,
                'corner_br': self.corner_br,
                'diag8': self.diag8,
                'diag7_tl': self.diag7_tl,
                'diag7_bl': self.diag7_bl,
            }
        else:
            self.patterns = {}

        # 重みの初期化（ファイルから読み込み or ランダム）
        if weights_path and Path(weights_path).exists():
            self.load_weights(weights_path)
        else:
            self._init_random_weights()

    def _init_random_weights(self) -> None:
        """重みをランダムに初期化。

        各パターンの状態数に合わせて重みの配列を作成。
        """
        self.weights = {}
        for pattern_name, squares in self.patterns.items():
            n_squares = len(squares)
            n_states = 3 ** n_squares
            self.weights[pattern_name] = np.zeros(n_states, dtype=np.float32)

    def pattern_index(
        self,
        board: list[list[int]],
        squares: list[tuple[int, int]],
        turn: int,
    ) -> int:
        """パターンのインデックスを計算（3 進数化）。

        Args:
            board: 盤面（0=空, -1=黒, 1=白）。
            squares: パターンに含まれるマスのリスト。
            turn: 手番プレイヤー（1=白, -1=黒）。

        Returns:
            3 進数インデックス（0 ～ 3^len(squares)-1）。
        """
        idx = 0
        for r, c in squares:
            v = board[r][c]
            # digit: 0=空, 1=turn 側, 2=相手側
            if v == 0:
                digit = 0
            elif v == turn:
                digit = 1
            else:
                digit = 2
            idx = idx * 3 + digit
        return idx

    def evaluate(
        self,
        board: list[list[int]],
        turn: int,
    ) -> float:
        """盤面をパターン評価で評価。

        Args:
            board: 盤面。
            turn: 手番プレイヤー。

        Returns:
            評価値（turn 側視点）。
        """
        score = 0.0
        for pattern_name, squares in self.patterns.items():
            if pattern_name not in self.weights:
                continue
            idx = self.pattern_index(board, squares, turn)
            score += float(self.weights[pattern_name][idx])
        return score

    def save_weights(self, path: str) -> None:
        """重みをファイルに保存（JSON 形式）。

        Args:
            path: 保存先パス（.json 推奨）。
        """
        # numpy 配列を list に変換して JSON 互換にする
        weights_dict = {}
        for pattern_name, arr in self.weights.items():
            weights_dict[pattern_name] = arr.tolist()

        with open(path, 'w') as f:
            json.dump(weights_dict, f)

    def load_weights(self, path: str) -> None:
        """重みをファイルから読み込み（JSON 形式）。

        Args:
            path: 読み込み元パス（.json）。
        """
        with open(path, 'r') as f:
            weights_dict = json.load(f)

        self.weights = {}
        for pattern_name, arr_list in weights_dict.items():
            self.weights[pattern_name] = np.array(arr_list, dtype=np.float32)

    def update_weight(
        self,
        board: list[list[int]],
        turn: int,
        pattern_name: str,
        delta: float,
    ) -> None:
        """特定パターンの重みを更新（TD 学習用）。

        Args:
            board: 盤面。
            turn: 手番プレイヤー。
            pattern_name: パターン名。
            delta: 加算値。
        """
        if pattern_name not in self.patterns:
            return
        squares = self.patterns[pattern_name]
        idx = self.pattern_index(board, squares, turn)
        self.weights[pattern_name][idx] += delta
