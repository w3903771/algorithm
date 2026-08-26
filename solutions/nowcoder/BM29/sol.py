# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/508378c0823c423baa723ce448cbfd0c
# 判题: 核心代码模式
# 签名: hasPathSum(root: TreeNode、sum: integer) -> boolean

"""BM29 二叉树中和为某一值的路径(一) —— 显式栈 DFS，边往下走边把 sum 减掉，到叶子看是否减到 0。

这题考什么：
    路径的定义是「根走到叶子」的完整一条，所以判定只能发生在叶子上，
    中途和恰好相等不作数。

    换一个记账方式能把状态变得极简：与其累加已经走过的和、再跟 sum 比，
    不如让 sum 一路做减法。走到某个节点时随身带一个 rest，含义是
    「从这里往下还需要凑出多少」；在这个节点减去它自己的值，剩下的
    rest 就是留给两棵子树各自的新目标。于是判定变成一句话：
    **走到叶子时 rest 恰好为 0**。

    rest 跟着节点一起放进栈里，是这份写法最省心的地方：DFS 用递归时
    「进入时加、退出时减」的回溯很容易漏掉一半，而把 rest 绑在栈元素上，
    每条分支各自持有自己的账，天然不会互相污染。

        示例 1 的 {5,4,8,1,11,#,9,#,#,2,7} 与 sum = 22：
            5 -> rest 22-5 = 17
            4 -> rest 17-4 = 13
            11 -> rest 13-11 = 2
            2 是叶子 -> rest 2-2 = 0，命中，返回 True

数据规模与复杂度：
    0 <= n <= 10000，每个节点的值满足 |val| <= 1000；时限「其他语言 2 秒」。
    最坏把每个节点访问一次，时间 O(n)；空间 O(n)，栈里最多同时存
    一条根到叶的路径分叉出来的兄弟分支。

坑在哪：
  1. **叶子判定必须「左右孩子都为空」**。只有一个孩子的节点不是叶子，
     在它那里凑够了也不算数。反例：树 {1,2}（根 1，左孩子 2）与 sum = 1，
     正确答案是 False（唯一的根到叶路径是 1 -> 2，和为 3）；若把「右孩子
     为空」就当叶子，根节点处 rest 恰好为 0，会误判成 True。
     示例 3 的 {1,2} 与 sum = 3 正好从另一面确认：路径必须走到 2 才算数。
  2. **空树一律返回 False，哪怕 sum 是 0**。示例 4 给的就是 {} 与 0，
     期望 false——空树里根本不存在「根到叶子」的路径，不是「和为 0 的空路径」。
  3. **不能按「rest 已经小于 0」剪枝**。节点值可以是负数，当前透支的部分
     完全可能被下面的负值拉回来，剪掉就漏解。这题唯一能提前退出的时机
     是命中一条合法路径。
  4. 叶子处不管命中与否都要 continue，不能落到下面的压孩子分支去——
     虽然叶子没有孩子、压不进东西，但显式 continue 才让「叶子是终点」
     这件事在代码里成立，也避免后续改动时多走一遍判空。
  5. n 到 1e4，链状树的递归深度就是 1e4，远超 CPython 默认的 1000 层上限，
     所以写成显式栈；三层限制见 docs/search/dfs.md 的 60.4 节。
"""
from typing import List, Optional


class Solution:
    def hasPathSum(self, root: "Optional[TreeNode]", sum: int) -> bool:
        # 空树没有任何「根到叶子」的路径，sum 取何值都是 False
        if root is None:
            return False
        stack = [(root, sum)]             # (当前节点, 从这里往下还需要凑出的值)
        while stack:
            node, rest = stack.pop()
            rest -= node.val              # 在本节点记账，剩下的留给两棵子树
            # 判定只发生在叶子上：中途凑够不算，凑不够也不能剪枝（值可为负）
            if node.left is None and node.right is None:
                if rest == 0:             # 只有叶子处凑满才算一条合法路径
                    return True
                continue                  # 叶子是终点，不再往下压
            # 每个孩子各自带走自己那份 rest，分支之间互不影响
            if node.left is not None:
                stack.append((node.left, rest))
            if node.right is not None:
                stack.append((node.right, rest))
        return False
