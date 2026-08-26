"""BM7 链表中环的入口结点 —— 判题驱动器（不含解法）。

样例输入是**两段**：`{1,2},{3,4,5}`——前段是环外的直链，后段是环本身。
后台把后段首尾相接成环、再挂到前段末尾；签名只有一个 `pHead`，看不出这回事。

期望输出是入口结点的**值**（`3`），或无环时的 `"null"`，不是链表序列，
所以这里返回值而不是节点。不用配 raw：默认比对会把两边都归一化，
`"null"` 与 None、字符串 `"3"` 与整数 3 都判等。
"""


def run(ns, input_text, codec):
    parts = codec.parse_nowcoder(input_text)
    before = parts[0] if parts else []
    loop = parts[1] if len(parts) > 1 else []

    a = [codec.ListNode(v) for v in (before or [])]
    b = [codec.ListNode(v) for v in (loop or [])]
    for x, y in zip(a, a[1:]):
        x.next = y
    for x, y in zip(b, b[1:]):
        x.next = y
    if b:
        b[-1].next = b[0]           # 后段自成环
    if a and b:
        a[-1].next = b[0]           # 直链挂到环入口
    head = (a or b or [None])[0]

    node = ns["Solution"]().EntryNodeOfLoop(head)
    return None if node is None else node.val
