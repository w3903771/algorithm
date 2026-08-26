"""BM6 判断链表中是否有环 —— 判题驱动器（不含解法）。

签名只有一个 `head`，但样例输入是**两段**：`{3,2,0,-4},1`
第二段是环入口的下标（-1 表示无环）。环是后台按这个下标接出来的，
签名里看不出这回事，所以通用 harness 只会把第一段当普通链表传进去，
永远无环——BM6 的正例必挂。这里照牛客的约定把环接上。
"""


def run(ns, input_text, codec):
    parts = codec.parse_nowcoder(input_text)
    vals = parts[0] if parts else []
    pos = parts[1] if len(parts) > 1 else -1

    nodes = [codec.ListNode(v) for v in (vals or [])]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and isinstance(pos, int) and 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    return ns["Solution"]().hasCycle(nodes[0] if nodes else None)
