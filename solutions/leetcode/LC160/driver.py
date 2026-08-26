"""LC160 相交链表 —— 判题驱动器（不含解法）。

metaData 列了五个参数 `intersectVal / listA / listB / skipA / skipB`，
但官方签名是 `getIntersectionNode(self, headA, headB)` 两个参数——
那五段是**搭相交结构用的描述**：listA 的前 skipA 个与 listB 的前 skipB 个各自独立，
之后共用同一批结点。通用 harness 会把两条链建成彼此独立的，正例永远判错。

相交的定义是**共享同一个结点对象**，不是值相等，所以公共段只造一份。
期望输出是散文 `Intersected at '8'` / `No intersection`，判题配 `mode: raw`。
"""


def run(ns, input_text, codec):
    inter, a_vals, b_vals, skip_a, skip_b = codec.split_params(
        input_text, 5, codec.LEETCODE)
    a_vals = list(a_vals or [])
    b_vals = list(b_vals or [])

    def chain(vals):
        nodes = [codec.ListNode(v) for v in vals]
        for x, y in zip(nodes, nodes[1:]):
            x.next = y
        return nodes

    # 公共段取 listA 从 skipA 起的那截，只造一份，两条链都接到它上面
    shared = chain(a_vals[skip_a:]) if skip_a < len(a_vals) else []
    only_a = chain(a_vals[:skip_a])
    only_b = chain(b_vals[:skip_b])
    if only_a:
        only_a[-1].next = shared[0] if shared else None
    if only_b:
        only_b[-1].next = shared[0] if shared else None
    head_a = only_a[0] if only_a else (shared[0] if shared else None)
    head_b = only_b[0] if only_b else (shared[0] if shared else None)

    got = ns["Solution"]().getIntersectionNode(head_a, head_b)
    if got is None:
        return "No intersection"
    return "Intersected at '%s'" % got.val
