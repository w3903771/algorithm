"""体检抓下来的题面：找出公式残缺、缺少输入/输出描述、缺样例等质量问题。

用法: uv run python scripts/check_problems.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "sources" / "05-nowcoder" / "raw"

# 被引号截断的公式：$ 后面紧跟一个未闭合的 \cmd{ 就直接遇到 $
TRUNC = re.compile(r"\$\\[a-zA-Z]+\{\$")
# 空公式或只剩控制序列
EMPTY_MATH = re.compile(r"\$\s*\$")


def main() -> int:
    issues = []
    files = sorted(RAW.glob("*.json"))
    for p in files:
        d = json.loads(p.read_text(encoding="utf-8"))
        no = p.stem
        blob = "\n".join([
            d.get("description", ""), d.get("inputDesc", ""), d.get("outputDesc", ""),
            *[e.get("note", "") for e in d.get("examples") or []],
        ])
        if TRUNC.search(blob):
            issues.append((no, "公式被截断", TRUNC.search(blob).group(0)))
        if EMPTY_MATH.search(blob):
            issues.append((no, "空公式", ""))
        if not d.get("description", "").strip():
            issues.append((no, "缺题目描述", ""))
        if not (d.get("examples") or []):
            issues.append((no, "缺样例", ""))
        for i, e in enumerate(d.get("examples") or [], 1):
            if not e.get("input", "").strip() and "无" not in e.get("input", ""):
                issues.append((no, f"样例{i} 输入为空", ""))
            if not e.get("output", "").strip():
                issues.append((no, f"样例{i} 输出为空", ""))

    print(f"体检 {len(files)} 份题面，发现 {len(issues)} 处问题")
    for no, kind, detail in issues:
        print(f"  {no:<10} {kind}  {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
