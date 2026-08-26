# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/8a19cbe657394eeaac2f6ea9b0f6fcf6
# 判题: 核心代码模式
# 签名: reConstructBinaryTree(preOrder: integer[]、vinOrder: integer[]) -> TreeNode

"""BM40 重建二叉树 —— 前序给根、中序切左右，用哈希表定位根下标后按区间迭代地拼。

这题考什么：
    单看任何一个遍历序列都还原不出树，两个序列各提供一半信息，合起来才唯一
    确定一棵树：**前序告诉你谁是根，中序告诉你根把哪些节点分到了左右两边**。

        前序 [1,2,4,7,3,5,6,8]   第一个元素一定是根
        中序 [4,7,2,1,5,3,8,6]   根把序列切成 [左子树][根][右子树]

        根 = 1，它在中序里的下标是 3 -> 左子树 3 个节点、右子树 4 个节点
        知道左子树大小，前序随即也能切:
            [1] [2,4,7] [3,5,6,8]
             根  左 3 个   右 4 个
        对两段重复同样的切分，整棵树就拼出来了。

    两个实现要点：
      1. **哈希表定位根**。每层都在中序里线性扫一遍找根是 O(n^2)，
         预先建「值 -> 中序下标」的字典，每层查根降到 O(1)，总复杂度 O(n)。
         题面保证两个序列都无重复元素，值才可以直接当键。
      2. **写成迭代**。栈里存「已经建好的节点 + 它负责的前序区间 + 中序区间」，
         弹出时用左子树大小把两个区间同步切开：
             左子树: 前序 [pl+1, pl+left]       中序 [il, k-1]
             右子树: 前序 [pl+left+1, pr]       中序 [k+1, ir]
         孩子非空就先按对应前序段的首元素 new 出来、挂到父亲身上，
         再连同区间一起入栈——出栈时父子关系已经接好，不必回填。

数据规模与复杂度：
    n <= 2000，节点值满足 -10000 <= val <= 10000 且无重复；时限「其他语言 2 秒」。
    每个节点建一次、入栈一次，查根 O(1)，时间 O(n)；
    空间 O(n)：下标字典 n 项，栈深等于树高。

坑在哪：
  1. **左子树大小要用中序下标算**：left = k - il，是「中序左段的长度」。
     直接拿 k 当长度只在 il == 0 时碰巧对，进入子区间后全线错位。
  2. 两个区间必须**同步**切分。前序段和中序段描述的是同一批节点，
     只要长度对上就一定对应；把前序的左段长度写成 k - il 之外的任何值，
     左右子树会互相偷节点，树形彻底乱掉。
  3. 右子树是否为空用中序侧的 ir - k > 0 判断，与左侧的 k - il 对称，
     不必再去前序区间上另算一遍长度。
  4. **哈希表不只是优化**。每层线性找根在链状树上是 O(n^2)：本题 n <= 2000
     还能扛（约 4e6 次比较），但同一套代码在 BM41 那里 n 到 1e4，
     O(n^2) 就是 1e8 次比较，Python 上必然超时。
  5. n <= 2000 已经超过 CPython 默认的 1000 层递归上限，链状树（前序与中序
     互为逆序时就是一条链）的递归深度就是 n，递归版会 RecursionError。
  6. 空数组返回 None。少了这道守卫，preOrder[0] 直接 IndexError。
  7. 值可以是负数（下界 -10000），所以任何「用 0 或 -1 表示空节点」的写法
     在这里都不成立，判空一律用 is None。
"""
from typing import Dict, List, Optional


class Solution:
    def reConstructBinaryTree(self, preOrder: List[int], vinOrder: List[int]) -> "Optional[TreeNode]":
        # 空序列对应空树；少了这一句下面取 preOrder[0] 会 IndexError
        if not preOrder:
            return None
        # 题面保证无重复元素，值才能当键；有了它每层找根从 O(n) 降到 O(1)
        pos: Dict[int, int] = {v: i for i, v in enumerate(vinOrder)}   # 值 -> 中序下标
        root = TreeNode(preOrder[0])
        # 栈元素: (已建好的节点, 它在前序里的区间 [pl, pr], 在中序里的区间 [il, ir])
        stack = [(root, 0, len(preOrder) - 1, 0, len(vinOrder) - 1)]
        while stack:
            node, pl, pr, il, ir = stack.pop()
            k = pos[node.val]                     # 根在中序里的位置
            left = k - il                         # 左子树节点个数
            # 左子树：前序段首元素就是它的根，先建好挂上再连区间入栈
            if left > 0:
                node.left = TreeNode(preOrder[pl + 1])
                stack.append((node.left, pl + 1, pl + left, il, k - 1))
            # 右子树：判空用中序侧的长度，与左侧的 k - il 对称
            if ir - k > 0:                        # 右子树节点个数 > 0
                node.right = TreeNode(preOrder[pl + left + 1])
                stack.append((node.right, pl + left + 1, pr, k + 1, ir))
        return root
