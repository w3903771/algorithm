"""BM43 包含 min 函数的栈 —— 判题驱动器（不含解法）。

操作序列同 BM42 的写法：`PSH<n>` / `POP` / `TOP` / `MIN`。
只有 TOP 与 MIN 有返回值，期望输出就是这些返回值按逗号拼接
（`["PSH-1","PSH2","MIN","TOP","POP","PSH1","TOP","MIN"]` -> `-1,2,1,-1`）。
"""


def run(ns, input_text, codec):
    ops = codec.parse_value(input_text, codec.NOWCODER) or []
    sol = ns["Solution"]()
    out = []
    for op in ops:
        op = str(op).strip()
        if op.startswith("PSH"):
            sol.push(int(op[3:]))
        elif op.startswith("POP"):
            sol.pop()
        elif op.startswith("TOP"):
            out.append(sol.top())
        elif op.startswith("MIN"):
            out.append(sol.min())
    return out
