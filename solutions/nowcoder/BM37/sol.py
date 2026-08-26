# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/d9820119321945f588ed6a26f0a6991f
# 判题: 核心代码模式
# 签名: lowestCommonAncestor(root: TreeNode、p: integer、q: integer) -> integer

"""BM37 二叉搜索树的最近公共祖先 —— 从根往下走，第一个夹在 p、q 之间的节点就是答案。

这题考什么：
    LCA（最近公共祖先）指同时是 p 和 q 的祖先、且深度尽可能大的那个节点；
    题面还额外约定「一个节点可以是它自己的祖先」。

    在普通二叉树里求 LCA 要先把两个节点定位出来再往上回溯（那是 BM38），
    但 BST（二叉搜索树）多了「值即位置」这条信息：只要比较值的大小，
    就知道一个节点在当前根的哪一侧。于是一次自根向下的行走就够了。
    站在 cur 上只有三种情况：

        p, q 都小于 cur.val   两个都在左子树，答案也在左子树   -> cur = cur.left
        p, q 都大于 cur.val   两个都在右子树                   -> cur = cur.right
        其余情况              分居两侧，或有一个正好等于 cur.val -> cur 就是答案

    第三种情况为什么能直接收：若 p、q 分居 cur 的两侧，再往任何一边走都会把
    另一个甩在外面，cur 是最后一个还能同时覆盖两者的节点；若其中一个恰好
    等于 cur.val，按「节点可以是自己的祖先」的约定，cur 已经是最深的公共祖先。

        示例 2 的 {7,1,12,0,4,11,14,#,#,3,5} 求 LCA(12, 11)：
        根 7，12 和 11 都比 7 大 -> 走右子树到 12；12 等于 p 本身，落进第三种
        情况，直接返回 12，与样例输出一致。

数据规模与复杂度：
    3 <= n <= 10000，节点值满足 0 <= val <= 10000 且互不相同；时限「其他语言 2 秒」。
    每一步都往下一层，时间 O(h)，h 为树高：随机 BST 约 O(log n)，
    链状 BST 退化到 O(n)。空间 O(1)，只用一个游标，没有栈也没有递归。

坑在哪：
  1. 前两个分支必须是**严格**的小于和大于。写成 `p <= cur.val and q <= cur.val`
     会在 p 恰好等于 cur.val 时继续往左走，把正确答案甩在身后——
     示例 2 就是这种「其中一个节点自己是答案」的情形，一放宽就会答成 11。
  2. 返回的是**节点值**，签名要求的是 integer 不是 TreeNode。返回节点对象
     会被判题按结构展开成一整棵树，比不上期望的那个整数。
  3. 不需要先确认 p、q 是否存在。题面保证两者都在树中，所以循环一定会在
     某个节点上撞进第三种情况并返回；函数末尾的 -1 只是兜底，让所有代码
     路径都有明确返回值，避免题面担保不成立时静默地返回 None。
  4. 这份写法天然是迭代的：每一步只把游标下移一层，既没有递归深度问题，
     也不需要显式栈——n 到 1e4 的链状 BST 用递归写就会撞上 CPython 默认的
     1000 层上限。
"""
from typing import List, Optional


class Solution:
    def lowestCommonAncestor(self, root: "Optional[TreeNode]", p: int, q: int) -> int:
        cur = root
        # 每轮只把游标下移一层，最多走树高那么多步
        while cur is not None:
            # 两个分支都必须是严格不等号：取等时 cur 自己就是答案
            if p < cur.val and q < cur.val:
                cur = cur.left            # 两个都更小，一起在左子树
            elif p > cur.val and q > cur.val:
                cur = cur.right           # 两个都更大，一起在右子树
            else:
                return cur.val            # 分居两侧，或撞上其中之一：就是它
        return -1                         # 题目保证有解，兜底不会走到
