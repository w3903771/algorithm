"""nc_html2md 公式转换的回归测试。

这些用例全部来自真实题面里踩过的坑，改解析器后务必先跑一遍：
  uv run python scripts/test_html2md.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nc_html2md import _img_to_text as f  # noqa: E402

CASES = [
    # (LaTeX 源码, 期望输出, 说明)
    (r"\hspace{15pt}", "", "纯缩进占位应丢弃"),
    (r"\quad", "", "纯 quad 应丢弃"),
    (r"{\hspace{22.5pt}}\bullet\ ", "\n- ", "项目符号（BISHI84/96/117 用到）"),
    (r"{}\circ", "\n- ", "空心项目符号"),
    (r"{\hspace{20pt}}_\texttt{1.}\,", "\n1. ", "有序列表标号"),
    (r"0", "$0$", "裸数字不能被当成排版占位（早期 bug）"),
    (r"i", "$i$", "单字母变量"),
    (r"\quad  2 \cdot \sum_{i=1}^{k} a_{p_i} > \sum_{i=1}^{n} a_i",
     r"$2 \cdot \sum_{i=1}^{k} a_{p_i} > \sum_{i=1}^{n} a_i$",
     "以 quad 起头的真公式必须保留（BISHI40 的核心约束曾整条丢失）"),
    (r'\texttt{"Yes"}', r'$\texttt{"Yes"}$', "含双引号（BISHI55 曾因 alt 被截断而丢失）"),
    (r"x \left( 1\leqq x \leqq 10^9 \right)", r"$x \left( 1\leqq x \leqq 10^9 \right)$",
     "带 \\left \\right 的区间"),
    (r"\hspace{15pt}\bullet\,\quad n \le 10^5", "\n- $n \\le 10^5$",
     "项目符号与正文公式在同一张图里"),
]


def main() -> int:
    bad = 0
    for tex, want, note in CASES:
        got = f(tex)
        ok = got == want
        if not ok:
            bad += 1
        print("[{}] {}\n      输入 {!r}\n      期望 {!r}\n      实际 {!r}".format(
            " ok " if ok else "FAIL", note, tex, want, got))
    print("\n{} 项通过 / {} 项失败".format(len(CASES) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
