"""training/alphazero/losses.py の TDD テスト"""
import pytest

TORCH_AVAILABLE = True
try:
    import torch
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestAlphaZeroLoss:
    def test_perfect_policy_zero_loss(self) -> None:
        """pi_target と logits が一致するとき policy_loss が小さい。"""
        from training.alphazero.losses import alphazero_loss
        logits = torch.zeros(2, 65)
        logits[:, 0] = 10.0  # action 0 に高スコア
        pi = torch.zeros(2, 65)
        pi[:, 0] = 1.0
        z = torch.zeros(2)
        v = torch.zeros(2, 1)
        total, policy_loss, value_loss = alphazero_loss(logits, v, pi, z)
        assert float(policy_loss) < 0.01

    def test_value_loss_zero_when_perfect(self) -> None:
        """v == z のとき value_loss == 0。"""
        from training.alphazero.losses import alphazero_loss
        logits = torch.zeros(2, 65)
        pi = torch.ones(2, 65) / 65
        z = torch.tensor([1.0, -1.0])
        v = z.unsqueeze(1)
        _, _, value_loss = alphazero_loss(logits, v, pi, z)
        assert float(value_loss) < 1e-6

    def test_backward_produces_gradients(self) -> None:
        """loss.backward() で全パラメータに grad が付く。"""
        from training.alphazero.losses import alphazero_loss
        from agents.networks.othello_net import OthelloNNet
        net = OthelloNNet(board_size=8)
        net.train()
        board = torch.randn(4, 1, 8, 8)
        logits, v = net(board)
        pi = torch.softmax(torch.randn(4, 65), dim=1)
        z = torch.tanh(torch.randn(4))
        total, _, _ = alphazero_loss(logits, v, pi, z)
        total.backward()
        for name, param in net.named_parameters():
            assert param.grad is not None, f"{name} に grad なし"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch が必要")
class TestCheckpoint:
    def test_save_load_roundtrip(self, tmp_path) -> None:
        """save_best → load_checkpoint でパラメータが一致する。"""
        from training.alphazero.checkpoint import save_best, load_checkpoint
        from agents.networks.othello_net import OthelloNNet
        import torch
        net1 = OthelloNNet(board_size=8)
        path = tmp_path / "test_model.pth"
        save_best(net1, path)
        net2 = OthelloNNet(board_size=8)
        load_checkpoint(net2, path)
        for (n1, p1), (n2, p2) in zip(net1.named_parameters(), net2.named_parameters()):
            assert torch.allclose(p1, p2), f"{n1} のパラメータが一致しない"
