"""BM30 二叉搜索树与双向链表 —— 判题驱动器（不含解法）。

签名说是 `Convert(TreeNode) -> TreeNode`，但返回的**不是树**：题目要求原地把
BST 改成双向链表，复用 TreeNode 的字段，`left` 当前驱、`right` 当后继。
通用编码器 `codec.dump_tree` 会沿 left/right 做层序 BFS，节点互相指回去，
队列无限膨胀，直接跑到超时——所以这题必须自己驱动。

期望输出也不是序列，而是牛客拼的一句话：

    From left to right are:4,6,8,10,12,14,16;From right to left are:16,14,12,10,8,6,4;

正向沿 `right` 走一遍、反向沿 `left` 走一遍，按这个格式拼出来即可。
两个方向都走能顺带验出指针接错的题解——只接对一边是常见错法。
"""


def _walk(node, attr, limit):
    """沿单向指针收值。limit 是保险丝：题解把链表接成环时不至于把判题机吊死。"""
    out = []
    while node is not None and len(out) <= limit:
        out.append(node.val)
        node = getattr(node, attr, None)
    return out


def run(ns, input_text, codec):
    seq = codec.parse_value(input_text, codec.NOWCODER)
    # 保险丝上限必须在 Convert **之前**算：Convert 是原地改指针，
    # 调用之后这棵树已经是双向链表了，再走 dump_tree 会自己陷进去。
    limit = sum(1 for v in (seq if isinstance(seq, list) else [seq]) if v is not None) + 5
    head = ns["Solution"]().Convert(codec.build_tree(seq))
    if head is None:
        return "From left to right are:;From right to left are:;"

    forward = _walk(head, "right", limit)
    tail = head
    seen = 0
    while getattr(tail, "right", None) is not None and seen <= limit:
        tail = tail.right
        seen += 1
    backward = _walk(tail, "left", limit)

    return ("From left to right are:" + ",".join(str(v) for v in forward) + ";"
            + "From right to left are:" + ",".join(str(v) for v in backward) + ";")
