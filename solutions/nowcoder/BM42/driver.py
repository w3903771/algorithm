"""BM42 用两个栈实现队列 —— 判题驱动器（不含解法）。

牛客把参数编进了操作名里：`["PSH1","PSH2","POP","POP"]`，
`PSH<n>` 是 push(n)、`POP` 是 pop()。期望输出是各次 pop 的返回值按逗号拼接。
签名里看不出这套规矩，所以单开驱动器。
"""


def run(ns, input_text, codec):
    ops = codec.parse_value(input_text, codec.NOWCODER) or []
    sol = ns["Solution"]()
    out = []
    for op in ops:
        op = str(op)
        if op.startswith("PSH"):
            sol.push(int(op[3:]))
        elif op.startswith("POP"):
            out.append(sol.pop())
    return out
