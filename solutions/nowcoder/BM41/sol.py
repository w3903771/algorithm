# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/c9480213597e45f4807880c763ddd5f0
# 判题: 核心代码模式
# 签名: solve(preOrder: integer[]、inOrder: integer[]) -> integer[]

"""BM41 输出二叉树的右视图 —— 先按前序+中序重建树，再层序遍历取每层最后一个节点。

这题考什么：
    签名收的不是树而是**两个数组**，所以它是两道题接在一起：
    先做一遍 BM40「重建二叉树」，再在还原出的树上求右视图。

    第一步 · 重建。前序首元素是根，它在中序里的下标把中序切成左右两段，
    左段长度同时也切开了前序，对两段重复即可。用「值 -> 中序下标」的哈希表
    把每层找根从 O(n) 降到 O(1)，整体 O(n)；用显式栈存「节点 + 前序区间 +
    中序区间」做成迭代。

    第二步 · 右视图。所谓右视图是「站在树的右边往左看，每层只看得见最右
    那一个节点」——注意是**每层的最右节点**，不是「从根一路往右走」：

        [1,2,4,5,3] / [4,2,5,1,3] 重建后
                1          第 1 层最右: 1
               / |
              2   3        第 2 层最右: 3
             / |
            4   5          第 3 层最右: 5      -> [1, 3, 5]

        节点 3 没有孩子，第 3 层能看见的是左子树里的 5。一路往右走会在 3 处
        停下，只得到 [1, 3]，与样例的 [1,3,5] 不符。

    所以按层做 BFS，每层取最后一个节点的值。这里用「整层推进」的写法：
    cur 里恰好是完整的一层，取 cur[-1].val，再把这一层的非空孩子按先左后右
    收集成下一层——顺序始终保持从左到右，末位自然就是最右节点。

数据规模与复杂度：
    0 <= n <= 10000，节点值在 [1, 10000] 且互不相同；时限「其他语言 2 秒」。
    重建 O(n) + 层序 O(n)，时间 O(n)；空间 O(n)：下标字典、重建栈、层数组
    各 O(n)。

坑在哪：
  1. **右视图不等于「一路向右」**。上面 [1,2,4,5,3] 的例子就是反例：
     右子树到第 2 层就断了，第 3 层露出来的是左子树的节点。
     只有按层扫才能保证每层都取到那个真正最右的节点。
  2. 收集下一层必须保持「先左后右」。顺序一旦颠倒，cur[-1] 取到的就成了
     每层的**最左**节点，等于求左视图。
  3. **哈希表定位根不是可选优化**。n 到 1e4，每层在中序里线性扫找根，
     链状树上是 1e8 次比较，Python 在 2 秒时限内跑不完（判题机还比本机慢
     数倍，本地耗时要按 3~4 倍留余量）。
  4. 递归重建同样不行：n 到 1e4，链状树的递归深度就是 1e4，远超 CPython
     默认的 1000 层上限，会 RecursionError；见
     docs/search/dfs.md 的 60.4 节。
  5. n 可以为 0，空数组返回 []。两道守卫缺一不可：_build 里挡住 preOrder[0]
     的 IndexError，solve 里挡住对 None 取 .val。
  6. 判题只调 solve，_build 是自己拆出来的辅助方法。签名约束只作用于
     模板给定的那个方法，辅助方法叫什么、放在哪都不影响判题。
"""
from typing import Dict, List, Optional


class Solution:
    def solve(self, preOrder: List[int], inOrder: List[int]) -> List[int]:
        root = self._build(preOrder, inOrder)
        # n 可以为 0；重建结果为空树时答案是 []
        if root is None:
            return []
        out: List[int] = []
        cur = [root]                              # cur 永远正好是完整的一层
        while cur:
            out.append(cur[-1].val)               # 该层最右的节点就是能看见的那个
            # 下一层按先左后右收集，顺序不能反，否则末位变成最左节点
            nxt: List["TreeNode"] = []
            for node in cur:
                if node.left is not None:
                    nxt.append(node.left)
                if node.right is not None:
                    nxt.append(node.right)
            cur = nxt
        return out

    def _build(self, preOrder: List[int], inOrder: List[int]) -> "Optional[TreeNode]":
        """前序 + 中序重建二叉树（同 BM40 的迭代版）。"""
        # 空序列对应空树；少了这一句下面取 preOrder[0] 会 IndexError
        if not preOrder:
            return None
        # 值互不相同才能当键；有了它每层找根是 O(1)，避免链状树上的 O(n^2)
        pos: Dict[int, int] = {v: i for i, v in enumerate(inOrder)}    # 值 -> 中序下标
        root = TreeNode(preOrder[0])
        # 栈元素: (已建好的节点, 前序区间 [pl, pr], 中序区间 [il, ir])
        stack = [(root, 0, len(preOrder) - 1, 0, len(inOrder) - 1)]
        while stack:
            node, pl, pr, il, ir = stack.pop()
            k = pos[node.val]
            left = k - il                         # 左子树节点个数
            # 左右两段的区间同步切分，长度对上了对应关系就一定对
            if left > 0:
                node.left = TreeNode(preOrder[pl + 1])
                stack.append((node.left, pl + 1, pl + left, il, k - 1))
            if ir - k > 0:
                node.right = TreeNode(preOrder[pl + left + 1])
                stack.append((node.right, pl + left + 1, pr, k + 1, ir))
        return root
