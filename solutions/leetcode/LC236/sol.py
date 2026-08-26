"""LC236 二叉树的最近公共祖先 —— 先记下每个节点的父指针，再让两条祖先链在最深处相遇。

这题考什么：
    LCA（最近公共祖先，Lowest Common Ancestor）是同时为 p 和 q 的祖先、
    且深度最大的那个节点；按题面的定义，一个节点也算它自己的祖先。

    教科书解法是一段极短的递归：在子树里找到 p 或 q 就往上报，
    某个节点的左右两侧各报回来一个，它就是答案。
    但这题节点数到 1e5，最坏是一条链，递归深度 1e5，
    远超 CPython 默认的 1000 层上限，那份递归在本题上跑不起来；
    递归改迭代见 docs/search/dfs.md 的 60.4 节。

    改成迭代，最直白的等价做法是**把树补成「可以往上走」的结构**：
        第一遍深度优先搜索（DFS），给每个节点记下它的父节点；
        从 p 出发沿父指针一路走到根，把整条祖先链装进集合；
        再从 q 出发沿父指针往上走，遇到的第一个在集合里的节点就是 LCA。

    正确性来自「从根到某节点的路径唯一」：两条祖先链都以根结尾，必然相交；
    而 q 这一侧是自底向上走的，第一次撞上 p 的链，撞点的深度必然最大。
    LCA 的其它路线（倍增、Tarjan、欧拉序加 ST 表）见
    docs/graph/tree/lca.md，那些是给多次查询准备的；
    本题只问一次，一遍 DFS 加两次上爬已经是最优。

    示例 2：root = [3,5,1,6,2,0,8,null,null,7,4]，p = 5、q = 4。
        5 的祖先链是 5 -> 3，装进集合
        从 4 往上：4 的父亲是 2，2 的父亲是 5 —— 5 在集合里，返回 5
    这正是「节点可以是自己的祖先」那一条的体现，与样例一致。

数据规模与复杂度：
    节点数在 [2, 10^5]，节点值在 [-10^9, 10^9] 且互不相同，p != q，
    题面保证 p 和 q 都存在于树中。
    一遍 DFS 建父指针 O(n)，两次向上走各不超过树高 O(h)，总时间 O(n)；
    空间 O(n)：父指针表最多 n 项，祖先集合最多 h 项。

坑在哪：
  1. **p、q 的传参形式在两处不一样，必须归一**。力扣官方模板写的是
     lowestCommonAncestor(self, root, p: 'TreeNode', q: 'TreeNode')，线上传的是
     两个**节点对象**；而题面 metaData 把这两个参数声明成 integer，
     本地判题按签名喂参，传进来的是两个**整数**。
     所以开头用 getattr(p, "val", p) 各取一次：拿到节点对象就取它的值，
     拿到整数就原样留着，两边都归一成「要找的节点值」。
     少了这一步，两个环境里必然有一个跑不对 —— 整数与 TreeNode 直接比较恒为假，
     两个目标节点都找不到，最后返回 None。
     题面保证所有 Node.val 互不相同，按值定位才没有歧义。
  2. **必须迭代**。1e5 个节点排成一条链时递归深度就是 1e5，递归版 RecursionError。
  3. **两个节点都找到就可以停**。用栈做 DFS 时，一个节点被弹出的那一刻，
     它的全部祖先都已经写进父指针表了（父指针是在展开父节点时写的），
     所以剩下的子树与答案无关。这是合法的提前退出，最坏情况仍是 O(n)。
  4. **祖先链要包含节点自身**。p 是 q 的祖先时（示例 2 就是），答案就是 p 本身；
     把自己漏在集合外，会一路爬到更浅的公共祖先，答案偏高一层。
  5. 父指针表与祖先集合都用节点的 id 当键。TreeNode 没有自定义相等与哈希，
     拿对象本身当键与拿 id 当键完全等价，写成 id 只是把「比的是同一个节点、
     而不是同一个值」讲明白。根不进父指针表，往上爬到它时 get 返回 None，
     循环自然停下，不需要额外的哨兵。
"""
from typing import List, Optional


class Solution:
    def lowestCommonAncestor(self, root: "Optional[TreeNode]", p: int, q: int) -> "Optional[TreeNode]":
        # 把两种传参形式归一成「要找的节点值」：力扣线上传节点对象，取它的 val；
        # 本地判题按 metaData 传整数，getattr 取不到 val 就原样返回它自己
        val_p = getattr(p, "val", p)
        val_q = getattr(q, "val", q)
        # id(子节点) -> 父节点对象。根不进表，爬到它时 get 得到 None，循环自然停
        parent = {}
        # 遍历途中按值把这两个目标节点的对象抓出来，后面要靠对象沿父指针上爬
        node_p = None
        node_q = None
        stack = [root]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            # 题面保证节点值互不相同，按值定位没有歧义
            if node.val == val_p:
                node_p = node
            if node.val == val_q:
                node_q = node
            # 提前退出：节点被弹出时它的整条祖先链已经登记完毕，剩下的子树与答案无关
            if node_p is not None and node_q is not None:
                break
            # 压孩子的同时把父指针写好，两件事必须一起做才不会漏登记
            if node.left is not None:
                parent[id(node.left)] = node
                stack.append(node.left)
            if node.right is not None:
                parent[id(node.right)] = node
                stack.append(node.right)
        # p 的整条祖先链，**含 p 自己** —— 「节点可以是自己的祖先」就靠这个「含自己」
        chain = set()
        cur = node_p
        while cur is not None:
            chain.add(id(cur))
            cur = parent.get(id(cur))
        # 从 q 自底向上爬，第一次撞进 p 的祖先链的那个节点深度最大，就是 LCA
        cur = node_q
        while cur is not None and id(cur) not in chain:
            cur = parent.get(id(cur))
        return cur
