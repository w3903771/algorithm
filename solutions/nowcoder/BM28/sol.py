# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/8a2b2bf6c19b4f23a9bdb9b233eefa73
# 判题: 核心代码模式
# 签名: maxDepth(root: TreeNode) -> integer

"""BM28 二叉树的最大深度 —— BFS 一层一层剥，剥掉几层深度就是几。

这题考什么：
    最大深度就是树的层数，所以「按层 BFS，数跑了多少轮」直接就是答案，
    根本不必求出每个节点的深度再取最大值。

    真正要考的是**规模意识**。递归版一行写完：
        depth(node) = 0 if node is None else 1 + max(depth(左), depth(右))
    但它的递归深度等于树高，而本题 n 到 1e5，树完全可以是一条
    1 -> 2 -> 3 -> ... -> 1e5 的链，树高就是 1e5。这份题解因此改成
    按层 BFS：cur 恰好装住当前层的全部节点，每换一层 depth 加一，
    某层为空就停，全程只有循环、没有函数调用，深度不受任何限制。

数据规模与复杂度：
    0 <= n <= 100000，节点值满足 |val| <= 100；时限「其他语言 2 秒」。
    每个节点被展开一次，时间 O(n)；空间 O(w)，w 是最宽一层的节点数，
    完全二叉树时约 n/2，也就是 5e4 个节点引用，离 512M 的空间限制很远。

    题面「要求」一栏写的是空间复杂度 O(1)，那是理想指标：任何普通遍历
    都做不到（递归版也要 O(h) 的栈），判题并不卡这一项。

坑在哪：
  1. **必须写迭代**。这是本专题最硬的一条：n 到 1e5 的链状树会让递归深度
     达到 1e5，而 CPython 的默认递归上限是 1000 层，直接 RecursionError；
     sys.setrecursionlimit 只放大计数器、不给 C 栈更多空间，撞破 C 栈是
     进程被操作系统杀掉，没有异常也没有 traceback，在牛客上表现成
     「运行错误」甚至「输出为空」，极难定位。三层限制的实测数据见
     docs/search/dfs.md 的 60.4 节。
  2. 深度按**节点数**算，不是边数：空树是 0，单节点是 1。所以 depth 从 0
     起步、在处理完一层之后才自增，而不是先加后处理。
  3. 空树守卫不能省。少了它 cur = [None]，第一轮取 node.left 就 AttributeError；
     而 n 可以为 0，空树是合法输入。
  4. 每轮必须把整层一次换掉（cur = nxt），不能在遍历 cur 的同时往 cur 里追加。
     边遍历边追加会把下一层混进本层，depth 只会加一次，答案恒为 1。
"""
from typing import List, Optional


class Solution:
    def maxDepth(self, root: "Optional[TreeNode]") -> int:
        # n 可以为 0；深度按节点数算，空树是 0 层
        if root is None:
            return 0
        depth = 0
        cur = [root]                      # cur 永远正好是「完整的一层」
        while cur:
            depth += 1                    # 又剥掉完整的一层
            # 整层重建：先收齐下一层再整体替换，不能边遍历 cur 边往里追加
            nxt: List["TreeNode"] = []
            for node in cur:
                if node.left is not None:
                    nxt.append(node.left)
                if node.right is not None:
                    nxt.append(node.right)
            cur = nxt
        return depth
