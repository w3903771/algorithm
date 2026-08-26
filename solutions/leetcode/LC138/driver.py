"""LC138 随机链表的复制 —— 判题驱动器（不含解法）。

不加驱动器时这题会**假通过**，比判错更危险：metaData 把参数类型写成 `ListNode`，
于是 `codec.shape` 拿 `[[7,null],[13,0],…]` 建出 5 个 val 是**列表**的普通结点，
random 指针整个丢失；此时一个原样返回入参的恒等函数照样能「通过」。

真实约定：结点是力扣的 `Node`（多一根 random 指针），输入的每一项是
`[val, randomIndex]`，randomIndex 为 null 表示 random 指向空。
输出按同样格式编码回去。

顺带查一件签名与样例都体现不出来、但题目真正要求的事：**必须是深拷贝**。
返回的结点若和原链共用对象，这里直接判错——否则「原样返回」也能骗过比对。
"""


def run(ns, input_text, codec):
    pairs = codec.parse_value(input_text, codec.LEETCODE) or []
    nodes = [ns["Node"](p[0]) for p in pairs]
    for i, (a, b) in enumerate(zip(nodes, nodes[1:])):
        a.next = b
    for n, p in zip(nodes, pairs):
        idx = p[1] if len(p) > 1 else None
        n.random = nodes[idx] if isinstance(idx, int) else None

    got = ns["Solution"]().copyRandomList(nodes[0] if nodes else None)

    origin = {id(n) for n in nodes}
    out, seen, cur = [], {}, got
    order = []
    while cur is not None and len(order) <= len(nodes) + 1:
        if id(cur) in origin:
            return "副本与原链共用了结点对象（要求深拷贝）"
        seen[id(cur)] = len(order)
        order.append(cur)
        cur = cur.next
    if len(order) != len(nodes):
        return f"副本长度 {len(order)}，原链长度 {len(nodes)}"
    for n in order:
        r = getattr(n, "random", None)
        if r is not None and id(r) in origin:
            return "random 指针指回了原链的结点（要求深拷贝）"
        out.append([n.val, seen.get(id(r)) if r is not None else None])
    return out
