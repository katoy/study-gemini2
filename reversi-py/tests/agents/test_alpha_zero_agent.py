"""AlphaZeroAgent（MCTS + PyTorch ResNet）のテスト。"""
import pytest

# PyTorch がインストール されているか確認
try:
    import torch  # noqa: F401
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


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not installed")
class TestAlphaZeroAgentEndgameSolver:
    """AlphaZeroAgent の終盤ソルバー機能のテスト。"""

    def test_solver_disabled_by_default(self) -> None:
        """デフォルトではソルバーが無効。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        agent = AlphaZeroAgent(n_simulations=10)
        assert agent._solver is None

    def test_endgame_uses_solver_not_mcts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """終盤局面（空きマス 12 以下）でソルバーが使用される。"""
        from unittest.mock import Mock
        from agents.alpha_zero_agent import AlphaZeroAgent
        from agents.alphazero.mcts import MCTS
        from agents.negamax_agent import NegamaxAgent
        from board import Board

        # ソルバー有効で初期化
        agent = AlphaZeroAgent(n_simulations=10, endgame_empties=12)
        assert agent._solver is not None

        # 終盤局面を構築（空きマス 12）
        board = [[0] * 8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                if (i, j) not in [(0, 0), (0, 1), (1, 0), (1, 1), (6, 6), (6, 7), (7, 6), (7, 7),
                                  (4, 4), (4, 5), (5, 4), (5, 5)]:
                    board[i][j] = -1
        board[0][0] = board[0][1] = board[1][0] = 1  # 白 3 石
        board[6][6] = board[6][7] = board[7][6] = 1  # 白 3 石
        board[4][4] = board[4][5] = board[5][4] = -1  # 黒 3 石
        board[5][5] = -1  # 黒 1 石

        # モック Game オブジェクトを作成
        game = Mock()
        game_board = Board(board_size=8)
        game_board.board = [row[:] for row in board]
        game.board = game_board
        game.turn = -1

        # NegamaxAgent.play と MCTS.run を監視
        solver_play_mock = Mock(return_value=(0, 0))
        monkeypatch.setattr(NegamaxAgent, 'play', solver_play_mock)
        mcts_run_mock = Mock()
        monkeypatch.setattr(MCTS, 'run', mcts_run_mock)

        agent.play(game)

        # ソルバーが呼ばれて MCTS は呼ばれない
        assert solver_play_mock.called
        assert not mcts_run_mock.called

    def test_midgame_uses_mcts_not_solver(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """中盤局面（空きマス > 12）では MCTS が使用される。"""
        from unittest.mock import Mock
        from agents.alpha_zero_agent import AlphaZeroAgent
        from agents.alphazero.mcts import MCTS
        from agents.negamax_agent import NegamaxAgent
        from game import Game

        # ソルバー有効で初期化
        agent = AlphaZeroAgent(n_simulations=5, endgame_empties=12)

        # 初期局面（空きマス 60）でプレイ
        game = Game(board_size=8)

        # NegamaxAgent.play と MCTS.run を監視
        solver_play_mock = Mock()
        monkeypatch.setattr(NegamaxAgent, 'play', solver_play_mock)
        mcts_run_mock = Mock(return_value={0: 10, 1: 5, 2: 3})
        monkeypatch.setattr(MCTS, 'run', mcts_run_mock)

        agent.play(game)

        # MCTS は呼ばれてソルバーは呼ばれない
        assert mcts_run_mock.called
        assert not solver_play_mock.called

    def test_endgame_solver_picks_winning_move(self) -> None:
        """終盤局面（空きマス <= 12）で正着を返す。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        from board import Board
        from unittest.mock import Mock

        # 終盤局面を構築（4x4、残り 1 マス）
        board = [
            [-1, -1, -1, -1],
            [-1, 1, 1, -1],
            [-1, 1, 0, -1],
            [-1, -1, -1, -1],
        ]

        # モック Game オブジェクトを作成
        game = Mock()
        game_board = Board(board_size=4)
        game_board.board = [row[:] for row in board]
        game.board = game_board
        game.turn = -1
        game.get_valid_moves.return_value = game_board.get_valid_moves(-1)

        # ソルバー有効で初期化
        agent = AlphaZeroAgent(n_simulations=5, board_size=4, endgame_empties=12)

        # play() を実行
        move = agent.play(game)

        # 合法手 (2, 2) が返される
        assert move == (2, 2)
        assert isinstance(move, tuple) and len(move) == 2

    def test_endgame_pass_returns_none(self) -> None:
        """終盤で合法手がない場合は None を返す。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        from board import Board
        from unittest.mock import Mock

        # 合法手がない局面（黒で埋め尽くし）
        board = [[-1] * 8 for _ in range(8)]

        # モック Game オブジェクトを作成
        game = Mock()
        game_board = Board(board_size=8)
        game_board.board = [row[:] for row in board]
        game.board = game_board
        game.turn = 1  # 白番
        game.get_valid_moves.return_value = game_board.get_valid_moves(1)

        # ソルバー有効で初期化
        agent = AlphaZeroAgent(n_simulations=5, endgame_empties=12)

        # play() を実行
        move = agent.play(game)

        # None が返される
        assert move is None

    def test_from_net_passes_solver_options(self) -> None:
        """from_net() クラスメソッドで endgame_empties が正しく伝搬される。"""
        from agents.alpha_zero_agent import AlphaZeroAgent
        from agents.networks.othello_net import OthelloNNet
        from agents.negamax_agent import NegamaxAgent

        # ネットワークを作成
        net = OthelloNNet(board_size=8)

        # endgame_empties=12 で初期化
        agent_with_solver = AlphaZeroAgent.from_net(
            net, n_simulations=10, endgame_empties=12
        )
        assert agent_with_solver._solver is not None
        assert isinstance(agent_with_solver._solver, NegamaxAgent)

        # endgame_empties=0 で初期化
        agent_without_solver = AlphaZeroAgent.from_net(
            net, n_simulations=10, endgame_empties=0
        )
        assert agent_without_solver._solver is None
