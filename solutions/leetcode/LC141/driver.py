"""LC141 环形链表 —— 判题驱动器（不含解法）。

**力扣的 metaData 描述的是判题输入格式，不是提交签名。** 这题的 metaData 写着
两个参数 `head` 与 `pos`，可官方 Python 模板是 `hasCycle(self, head)` 一个参数：
`pos` 是「环入口下标」，环由判题后台照它接好，不会作为实参传给题解。

通用 harness 按 metaData 喂两个参数，必然 TypeError；就算只喂一个，
建出来的也是一条**无环**直链，正例永远判错。所以这题得自己驱动。
"""


def run(ns, input_text, codec):
    vals, pos = codec.split_params(input_text, 2, codec.LEETCODE)
    nodes = [codec.ListNode(v) for v in (vals or [])]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and isinstance(pos, int) and 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]          # pos = -1 表示无环
    return bool(ns["Solution"]().hasCycle(nodes[0] if nodes else None))
