# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/91b69814117f4e8097390d107d2efbe0
# 判题: 核心代码模式
# 签名: Print(pRoot: TreeNode) -> list<list<integer>>

"""BM27 按之字形顺序打印二叉树 —— 照常层序 BFS，只把奇数层那一行翻过来。

这题考什么：
    第一反应往往是「用两个栈交替」，但那是把问题想复杂了。
    之字形只改变**每一行内部的输出顺序**，完全不改变遍历本身：
    树的形状没变，每层由哪些节点组成也没变，变的只是这些值怎么排。

    于是解法 = BM26 的整层 BFS + 一个方向开关：
      1. cur 恰好装住当前层的全部节点，始终按从左到右的顺序；
      2. 收行时看层号，偶数层原样收，奇数层把这一行 reverse；
      3. 下一层仍按「先左后右」从 cur 收集，与方向开关无关。

        示例 2 的 {8,6,10,5,7,9,11}：
            第 0 层 [8]              -> 行 [8]
            第 1 层 [6, 10]          -> 翻转 -> 行 [10, 6]
            第 2 层 [5, 7, 9, 11]    -> 行 [5, 7, 9, 11]
        结果 [[8],[10,6],[5,7,9,11]]，与样例输出一致。

    层序 BFS 的框架见 docs/search/bfs.md。

数据规模与复杂度：
    0 <= n <= 1500，节点值满足 |val| <= 1500；时限「其他语言 2 秒」。
    每个节点被收集一次、被展开一次，所有行的翻转加起来也只碰每个值一次，
    时间 O(n)；空间 O(w)，w 是最宽一层的节点数。

坑在哪：
  1. **只翻输出行，不翻节点收集顺序**。这是本题唯一真正的陷阱：
     若把 cur 本身也倒过来，下一层的孩子就会按右到左收集。示例 2 里
     第 1 层变成 [10, 6] 后，第 2 层会收成 [9, 11, 5, 7]，与期望的
     [5, 7, 9, 11] 完全不同——错在第三层才暴露，比错在第二层更难查。
  2. `row.reverse()` 是原地翻转、返回 None。写成 `out.append(row.reverse())`
     会往答案里塞一个 null。要么先 reverse 再 append，要么用 row[::-1]。
  3. 方向开关的初值对应「第 0 层不翻」。根这一行只有一个元素，翻不翻看不出
     区别，一旦初值取反，从第 1 层起每行都是反的，示例 1 就会挂。
  4. 用布尔开关取反，比每轮拿 len(out) % 2 去算层号更不容易写错——
     后者要留意 append 发生在取模之前还是之后。
  5. 空树是合法输入（n 可以为 0），期望 []。
"""
from typing import List, Optional


class Solution:
    def Print(self, pRoot: "Optional[TreeNode]") -> List[List[int]]:
        # n 可以为 0，空树的答案是 []
        if pRoot is None:
            return []
        out: List[List[int]] = []
        cur = [pRoot]
        left_to_right = True              # 第 0 层从左到右
        while cur:
            # cur 始终是从左到右的一层，取值后按层号决定这一行要不要倒过来
            row = [node.val for node in cur]
            if not left_to_right:
                row.reverse()             # 只翻这一行的输出，不动节点顺序
            out.append(row)
            left_to_right = not left_to_right   # 逐层交替方向
            # 方向开关只作用于上面的输出行，收集下一层与它无关
            nxt: List["TreeNode"] = []
            for node in cur:              # 下一层始终按「先左后右」收集
                if node.left is not None:
                    nxt.append(node.left)
                if node.right is not None:
                    nxt.append(node.right)
            cur = nxt
        return out
