"""LC142 环形链表 II —— 判题驱动器（不含解法）。

与 LC141 同源：metaData 的第二个参数 `pos` 是环入口下标，由后台接环，
官方签名 `detectCycle(self, head)` 只收一个参数。

另有一层：期望输出不是链表也不是下标，而是一句中文散文——
`返回索引为 1 的链表节点` / `返回 null`。所以驱动器返回同样格式的句子，
判题配 `mode: raw` 按原始文本比。

返回的必须是**入口结点本身**，不是值相等的另一个结点：这里按对象身份
（`is`）去原链表里找下标，题解若新建了结点就会落到「未在链表中」而判错。
"""


def run(ns, input_text, codec):
    vals, pos = codec.split_params(input_text, 2, codec.LEETCODE)
    nodes = [codec.ListNode(v) for v in (vals or [])]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and isinstance(pos, int) and 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]

    got = ns["Solution"]().detectCycle(nodes[0] if nodes else None)
    if got is None:
        return "返回 null"
    for i, n in enumerate(nodes):
        if n is got:                          # 身份比对，不是值比对
            return f"返回索引为 {i} 的链表节点"
    return "返回了不属于原链表的结点"
