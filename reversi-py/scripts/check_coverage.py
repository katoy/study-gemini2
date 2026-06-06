#!/usr/bin/env python3
"""カバレッジが 100% であることを確認（GUI を除外）"""
import json
import sys

with open('coverage.json', 'r') as f:
    data = json.load(f)

missing_coverage = []
for file, coverage_info in data['files'].items():
    if 'gui.py' not in file and 'modal_dialog.py' not in file:
        coverage = coverage_info['summary']['percent_covered']
        if coverage < 100:
            missing_coverage.append((file, coverage))

if missing_coverage:
    print("❌ 100% カバレッジ未達のファイル:")
    for file, coverage in sorted(missing_coverage):
        print(f"  {file}: {coverage:.1f}%")
    sys.exit(1)
else:
    print("✅ GUI 以外のすべてのファイルが 100% カバレッジを達成しています")
    sys.exit(0)
