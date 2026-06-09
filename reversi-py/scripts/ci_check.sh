#!/bin/bash
# CI チェックスクリプト
# ローカルで GitHub Actions と同等のチェックを実行

set -e

echo "================================"
echo "CI チェック スタート"
echo "================================"
echo

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# チェック結果
FAILED=0

# 1. Lint チェック (ruff)
echo -e "${YELLOW}[1/4] Lint チェック (ruff)${NC}"
if uv run ruff check . --select=E,W,F --exclude=tests; then
    echo -e "${GREEN}✅ Lint チェック: 成功${NC}"
else
    echo -e "${RED}❌ Lint チェック: 失敗${NC}"
    FAILED=1
fi
echo

# 2. 型チェック (mypy)
echo -e "${YELLOW}[2/4] 型チェック (mypy)${NC}"
if uv run mypy . --ignore-missing-imports; then
    echo -e "${GREEN}✅ 型チェック: 成功${NC}"
else
    echo -e "${RED}❌ 型チェック: 失敗${NC}"
    FAILED=1
fi
echo

# 3. テスト実行
echo -e "${YELLOW}[3/4] テスト実行${NC}"
if uv run pytest -q; then
    echo -e "${GREEN}✅ テスト: 成功${NC}"
else
    echo -e "${RED}❌ テスト: 失敗${NC}"
    FAILED=1
fi
echo

# 4. カバレッジ チェック（GUI 除外）
echo -e "${YELLOW}[4/4] カバレッジ チェック（GUI 除外）${NC}"
echo "計測対象: GUI 以外は 100%"

# カバレッジ計測
COVERAGE_REPORT=$(uv run pytest --cov=. --cov-report=term-missing:skip-covered \
    --ignore=tests/test_gui.py \
    --ignore=tests/test_gui_regression.py \
    --ignore=tests/test_gui_width.py \
    -q 2>&1)

echo "$COVERAGE_REPORT" | tail -30

# カバレッジ 100% 確認（GUI 除外後）
COVERAGE_LINE=$(echo "$COVERAGE_REPORT" | grep "^TOTAL")
COVERAGE_PERCENT=$(echo "$COVERAGE_LINE" | awk '{print $NF}' | sed 's/%//')

if [ -z "$COVERAGE_PERCENT" ]; then
    echo -e "${RED}❌ カバレッジ計測: 失敗${NC}"
    FAILED=1
elif [ "${COVERAGE_PERCENT%.*}" -lt 100 ]; then
    echo -e "${RED}❌ カバレッジ 100% 未達: ${COVERAGE_PERCENT}%${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ カバレッジ: ${COVERAGE_PERCENT}% (100% 達成)${NC}"
fi
echo

# 最終結果
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ CI チェック: 全て成功${NC}"
    echo "================================"
    exit 0
else
    echo -e "${RED}❌ CI チェック: 失敗あり${NC}"
    echo "================================"
    exit 1
fi
