"""BISHI96 先序遍历、中序遍历和后序遍历 —— 由 n-1 条有向父子边建二叉树并输出三种遍历。

这题考什么：
    建树 + 三种 DFS 遍历。难点全在「左右孩子怎么定」和「n = 1e5 的递归深度」。

    左右孩子规则（题面原文）：
      - 父节点有两个孩子：编号**较小**者为左孩子，较大者为右孩子；
      - 父节点只有一个孩子：该孩子编号**大于**父节点编号 -> 左孩子，否则右孩子。
    根节点 = 入度为 0 的那个点（没有出现在任何 b_i 里）。

数据规模与复杂度：
    n <= 1e5。建树 O(n)，三次遍历各 O(n)。

Python 的坑（本题必看）：
  1. **递归必须改成显式栈**。这棵树可以退化成一条长度 1e5 的链
     （比如 1->2->3->...->n），递归 DFS 的深度就是 1e5，
     远超 CPython 默认 1000 层的上限；即使 setrecursionlimit 调大，
     C 栈也很可能直接崩掉。所以三种遍历全部写成迭代版：
       - 先序：栈里先压右孩子再压左孩子，出栈即访问；
       - 中序：经典「一路向左压栈 -> 弹出访问 -> 转向右子树」；
       - 后序：用「根-右-左」的先序变体，最后整体 reverse，
         比双栈 / 标记法更短也更快。
     （另一条路是 threading.stack_size(1<<26) + setrecursionlimit 开大栈线程，
       但要多起一个线程、代码更绕，这里不用。）
  2. 输出三行、每行 1e5 个数，用 " ".join(map(str, ...)) 拼好再一次 write。

坑在哪：
  1. n = 1 时没有任何边，根就是 1，三行都输出 "1"；
  2. 单孩子的判定基准是「孩子编号 vs 父节点编号」，
     不是「孩子编号 vs 兄弟」，也不是固定放左边；
  3. 题面保证是二叉树，所以每个父节点至多两个孩子，不必额外校验。

样例复核：
    n=2，边 1->2。父 1 只有一个孩子 2，且 2 > 1 -> 左孩子。
    先序 = 1 2；中序 = 左(2) 根(1) = 2 1；后序 = 左(2) 根(1) = 2 1，与样例一致。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    left = [0] * (n + 1)
    right = [0] * (n + 1)
    kids = [[] for _ in range(n + 1)]
    has_parent = bytearray(n + 1)

    p = 1
    for _ in range(n - 1):
        a = int(data[p]); b = int(data[p + 1]); p += 2
        kids[a].append(b)
        has_parent[b] = 1

    for u in range(1, n + 1):
        ch = kids[u]
        if len(ch) == 2:
            x, y = ch
            if x > y:
                x, y = y, x
            left[u], right[u] = x, y          # 两个孩子：小的在左
        elif len(ch) == 1:
            v = ch[0]
            if v > u:
                left[u] = v                   # 独子且编号大于父 -> 左
            else:
                right[u] = v

    root = 1
    for u in range(1, n + 1):
        if not has_parent[u]:
            root = u
            break

    # ---- 先序：根 左 右（栈里反着压） ----
    pre = []
    st = [root]
    while st:
        u = st.pop()
        pre.append(u)
        r = right[u]
        if r:
            st.append(r)
        l = left[u]
        if l:
            st.append(l)

    # ---- 中序：一路向左压栈，弹出访问后转右子树 ----
    ino = []
    st = []
    u = root
    while st or u:
        while u:
            st.append(u)
            u = left[u]
        u = st.pop()
        ino.append(u)
        u = right[u]

    # ---- 后序：先按「根 右 左」跑一遍先序，再整体逆序 ----
    post = []
    st = [root]
    while st:
        u = st.pop()
        post.append(u)
        l = left[u]
        if l:
            st.append(l)
        r = right[u]
        if r:
            st.append(r)
    post.reverse()

    w = sys.stdout.write
    w(" ".join(map(str, pre)) + "\n")
    w(" ".join(map(str, ino)) + "\n")
    w(" ".join(map(str, post)) + "\n")


main()
