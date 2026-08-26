"""BM10 两个链表的第一个公共结点 —— 判题驱动器（不含解法）。

样例输入是**三段**：`{1,2,3},{4,5},{6,7}`——链1独有、链2独有、两者共用。
后台把第三段拼成 Y 型的公共尾巴，两条链**共享同一批节点对象**（不是值相等）。
签名只有两个 `pHead1/pHead2`，通用 harness 会把前两段当成两条独立链，
公共段整个丢掉，正例必挂。
"""


def _chain(vals, codec):
    nodes = [codec.ListNode(v) for v in (vals or [])]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    return nodes


def run(ns, input_text, codec):
    parts = codec.parse_nowcoder(input_text)
    while len(parts) < 3:
        parts.append([])
    only1, only2, common = parts[0], parts[1], parts[2]

    shared = _chain(common, codec)      # 公共段只造一份，两条链都指向它
    a = _chain(only1, codec)
    b = _chain(only2, codec)
    if a:
        a[-1].next = shared[0] if shared else None
    if b:
        b[-1].next = shared[0] if shared else None
    head1 = a[0] if a else (shared[0] if shared else None)
    head2 = b[0] if b else (shared[0] if shared else None)

    return codec.dump_list(ns["Solution"]().FindFirstCommonNode(head1, head2))
