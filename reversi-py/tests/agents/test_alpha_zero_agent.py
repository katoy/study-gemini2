"""AlphaZeroAgent（MCTS + PyTorch ResNet）のテスト。"""
import pytest

# PyTorch がインストール されているか確認
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
class TestReversiNet:
    """ReversiNet（ResNet ベース）のテスト。"""

    def test_reversi_net_import(self) -> None:
        """ReversiNet がインポート可能。"""
        from agents.networks.reversi_net import ReversiNet
        net = ReversiNet(board_size=8)
        assert net is not None

    def test_reversi_net_forward_shape(self) -> None:
        """forward パスの出力形状が正しい。"""
        import torch
        from agents.networks.reversi_net import ReversiNet

        net = ReversiNet(board_size=8, n_res_blocks=2, n_filters=32)
        x = torch.zeros(1, 2, 8, 8)
        policy, value = net(x)

        assert policy.shape == (1, 65)  # 8*8 + 1 (パス)
        assert value.shape == (1, 1)

    def test_reversi_net_value_range(self) -> None:
        """value head の出力が [-1, 1] の範囲。"""
        import torch
        from agents.networks.reversi_net import ReversiNet

        net = ReversiNet(board_size=8)
        x = torch.randn(4, 2, 8, 8)
        _, value = net(x)

        assert value.abs().max() <= 1.0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
class TestAlphaZeroAgent:
    """AlphaZeroAgent（MCTS + NN）のテスト。"""

    def test_agent_initialization(self) -> None:
        """エージェントが初期化できる。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        agent = AlphaZeroAgent(n_simulations=10)
        assert agent is not None

    def test_agent_play_returns_valid_move(self) -> None:
        """play() が合法手またはパスを返す。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        from game import Game

        agent = AlphaZeroAgent(n_simulations=5)
        game = Game(board_size=8)
        move = agent.play(game)

        assert move is None or (isinstance(move, tuple) and len(move) == 2)
