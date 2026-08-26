# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/e0cc33a83afe4530bcec46eba3325116
# 判题: 核心代码模式
# 签名: lowestCommonAncestor(root: TreeNode、o1: integer、o2: integer) -> integer

"""BM38 在二叉树中找到两个节点的最近公共祖先 —— 先记下每个节点的父指针，再让两条祖先链相遇。

这题考什么：
    LCA（最近公共祖先）在普通二叉树上没有 BM37 那种「按值决定往哪边走」的
    便利：这里的树不是 BST（二叉搜索树），值的大小和位置毫无关系，
    只能真的把两个节点找出来。

    最直白且完全不吃递归栈的路线是**建父指针 + 走祖先链**，把树问题降成
    链表问题——两条祖先链最终都通向根，问题就变成「两条链的第一个公共节点」：

      1. 一次遍历，记下 parent[值] = 父节点的值（根记 None）；
      2. 从 o1 出发沿 parent 一路往上，把整条祖先链塞进集合 seen，
         **包含 o1 自己**（题面明确「节点本身可以视为自己的祖先」）；
      3. 从 o2 出发同样往上走，**第一个**落在 seen 里的值就是 LCA。

        {3,5,1,6,2,0,8,#,#,7,4} 求 LCA(7, 1)
        7 的祖先链: 7 -> 2 -> 5 -> 3      seen = {7, 2, 5, 3}
        1 的祖先链: 1 -> 3                1 不在 seen，3 在 -> 答案 3

    第 3 步为什么「第一个命中」就是「最近」：从 o2 往上走深度是严格递减的，
    最先撞上的那个公共节点自然深度最大，正合 LCA 的定义。

数据规模与复杂度：
    1 <= n <= 1e5，节点值在 [0, n) 且互不相同；时限「其他语言 2 秒」。
    建表遍历一次 O(n)，两条祖先链最长各 O(n)（链状树），
    集合的查与插都是均摊 O(1)，总时间 O(n)；空间 O(n)，parent 表加 seen 集合。

坑在哪：
  1. **祖先链必须包含节点自己**。示例 2 求 LCA(2, 7)，7 的祖先链上第一个
     公共节点就是 2 本身；若 seen 从 parent[o1] 开始建，2 不在集合里，
     会一路答成 5。题面那句「节点本身可以视为自己的祖先」就是冲这里来的。
  2. **拿 val 当键的前提是题面保证节点值互不相同**，这一条题面写明了。
     换成允许重复值的树（比如 BM36 那题的值域），键必须改成 id(node)，
     否则两个同值节点会在 parent 表里互相覆盖。
  3. parent[root] 必须显式记成 None，它是两条上行循环的终止条件。
     不记这一项，走到根时 `parent[cur]` 直接 KeyError。
  4. n 到 1e5 且树可能退化成一条链，**遍历和上行都必须是循环**。
     递归版的深度就是 1e5，远超 CPython 默认的 1000 层上限，会 RecursionError；
     调大计数器也救不了 C 栈，见 docs/search/dfs.md 的 60.4 节。
  5. 建表用的显式栈是前序还是别的顺序无所谓——只要每个节点都被访问到，
     父指针就记全了，这一步不依赖任何遍历次序。
  6. 返回的是节点值（签名要求 integer）。末尾的 -1 是兜底：两个节点同处
     一棵树必然在根之前相遇，正常数据走不到那一行。
"""
from typing import Dict, List, Optional


class Solution:
    def lowestCommonAncestor(self, root: "Optional[TreeNode]", o1: int, o2: int) -> int:
        if root is None:
            return -1
        # 第一步：一次遍历记全父指针。根的父记 None，作为上行的终止标记
        parent: Dict[int, Optional[int]] = {root.val: None}
        stack = [root]
        while stack:                          # 迭代遍历，把父指针记全
            node = stack.pop()
            # 顺序无所谓：只要每个节点都到过，parent 就是完整的
            for child in (node.left, node.right):
                if child is not None:
                    parent[child.val] = node.val
                    stack.append(child)

        # 第二步：把 o1 的整条祖先链存起来，必须含 o1 自己
        seen = set()
        cur: Optional[int] = o1
        while cur is not None:                # o1 的整条祖先链（含它自己）
            seen.add(cur)
            cur = parent[cur]

        # 第三步：o2 往上走，深度递减，所以第一个命中的就是最深的公共祖先
        cur = o2
        while cur is not None:                # o2 往上，第一个命中的最深
            if cur in seen:
                return cur
            cur = parent[cur]
        return -1                             # 同处一棵树必相遇，兜底不会走到
