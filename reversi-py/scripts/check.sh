#!/bin/bash
# CI チェック用スクリプト（GitHub Actions と同等）

set -e

echo "================================"
echo "CI チェックを開始します"
echo "================================"

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# エラーカウンター
ERRORS=0

# 1. Ruff Lint チェック
echo ""
echo -e "${YELLOW}[1/5] Ruff Lint チェック...${NC}"
if uv run ruff check .; then
    echo -e "${GREEN}✅ Ruff: OK${NC}"
else
    echo -e "${RED}❌ Ruff: NG${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Mypy 型チェック
echo ""
echo -e "${YELLOW}[2/5] Mypy 型チェック...${NC}"
if uv run mypy . --ignore-missing-imports; then
    echo -e "${GREEN}✅ Mypy: OK${NC}"
else
    echo -e "${RED}❌ Mypy: NG${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 3. Pytest テスト実行
echo ""
echo -e "${YELLOW}[3/5] Pytest テスト実行...${NC}"
if command -v xvfb-run &> /dev/null; then
    # Xvfb が利用可能な場合（Linux）
    if xvfb-run -a uv run pytest tests/ --cov=. --cov-report=json --cov-config=.coveragerc -q; then
        echo -e "${GREEN}✅ Tests: OK${NC}"
    else
        echo -e "${RED}❌ Tests: NG${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    # Xvfb が利用できない場合（macOS など）
    if SDL_VIDEODRIVER=dummy uv run pytest tests/ --cov=. --cov-report=json --cov-config=.coveragerc -q; then
        echo -e "${GREEN}✅ Tests: OK${NC}"
    else
        echo -e "${RED}❌ Tests: NG${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 4. GUI 起動テスト
echo ""
echo -e "${YELLOW}[4/5] GUI 起動テスト...${NC}"
if command -v xvfb-run &> /dev/null; then
    # Xvfb が利用可能な場合
    if xvfb-run -a uv run python scripts/test_gui_init.py; then
        echo -e "${GREEN}✅ GUI Init: OK${NC}"
    else
        echo -e "${RED}❌ GUI Init: NG${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    # Xvfb が利用できない場合
    if SDL_VIDEODRIVER=dummy uv run python scripts/test_gui_init.py; then
        echo -e "${GREEN}✅ GUI Init: OK${NC}"
    else
        echo -e "${RED}❌ GUI Init: NG${NC}"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 5. カバレッジ 100% チェック
echo ""
echo -e "${YELLOW}[5/5] カバレッジ 100% チェック...${NC}"
if uv run python scripts/check_coverage.py; then
    echo -e "${GREEN}✅ Coverage: OK${NC}"
else
    echo -e "${RED}❌ Coverage: NG${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 結果表示
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ すべてのチェックに合格しました${NC}"
    echo "================================"
    exit 0
else
    echo -e "${RED}❌ $ERRORS 個のチェックが失敗しました${NC}"
    echo "================================"
    exit 1
fi
