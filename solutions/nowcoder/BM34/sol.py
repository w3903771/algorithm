# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/a69242b39baf45dea217815c7dedb52b
# 判题: 核心代码模式
# 签名: isValidBST(root: TreeNode) -> boolean

"""BM34 判断是不是二叉搜索树 —— 中序遍历一遍，看序列是不是严格递增。

这题考什么：
    BST（二叉搜索树）的定义是「左子树上的**所有**节点都小于当前节点，
    右子树上的所有节点都大于当前节点」。最容易写错的判法是只看父子三点：
    node.left.val < node.val < node.right.val。这个条件对每个节点都成立，
    树也未必是 BST——约束的对象是整棵子树，不是直接孩子：

        树 {10, 5, 15, #, #, 6, 20}
                10
               /  |
              5    15
                  /  |
                 6    20
        父子三点全都合法（6 < 15 < 20），但 6 在 10 的右子树里却比 10 小，不是 BST。

    真正的等价刻画是：**BST 的中序遍历是严格递增序列**。
    中序按「左 -> 根 -> 右」走，正好把「左子树全部小于根、根小于右子树全部」
    摊平成一条线，于是只要相邻两项都满足 prev < cur，全局约束自动满足，
    既不用传上下界，也不用为每个节点单独求子树最值。

    实现是标准的迭代中序：一路向左压栈，弹出栈顶即中序的下一个节点，
    拿它的值和前驱比，然后转向它的右孩子。

数据规模与复杂度：
    1 <= n <= 1e4，节点值满足 -2^31 <= val <= 2^31 - 1；时限「其他语言 2 秒」。
    每个节点入栈出栈各一次，时间 O(n)；空间 O(h)，h 为树高，链状树退化到 O(n)。

坑在哪：
  1. **比较对象是中序前驱，不是父节点**。上面那棵 {10,5,15,#,#,6,20} 就是
     专门用来打掉「只比父子」写法的：6 的父亲是 15，父子关系挑不出毛病，
     但 6 的中序前驱是 10，一比就露馅。
  2. **必须严格递增**。题面写的是「均小于」「均大于」，等号不允许，
     所以判否的条件是 prev >= cur.val。写成 prev > cur.val 会把含相等值的
     树误判成 BST。
  3. **哨兵不能取具体数字**。节点值下界就是 -2^31，拿 -2^31 或 -10^9 当
     prev 的初值，遇到根左端恰好是这个值的树就会在第一次比较时误判成 False。
     Python 里 float("-inf") 可用，但 None 完全不依赖值域，读起来也直白：
     `prev is not None` 就是「已经有前驱了」。
  4. 发现逆序立即返回 False。这是合法的提前退出：中序序列一旦出现非递增，
     后面无论怎样都救不回来，没有必要遍历完。
  5. n 到 1e4，链状树的递归深度就是 1e4，远超 CPython 默认的 1000 层上限，
     所以中序写成显式栈；三层限制见 docs/search/dfs.md 的 60.4 节。
  6. 题面保证 n >= 1，这份写法对空树也返回 True：两个循环条件同时不成立，
     直接落到 return True，与「空树是 BST」的通常约定一致。
"""
from typing import List, Optional


class Solution:
    def isValidBST(self, root: "Optional[TreeNode]") -> bool:
        stack: List["TreeNode"] = []
        cur = root
        prev = None                       # 中序里的前一个值，None 表示还没有前驱
        # 迭代中序：出栈顺序就是升序检查的顺序
        while cur is not None or stack:
            while cur is not None:        # 一路向左，把沿途节点压栈
                stack.append(cur)
                cur = cur.left
            node = stack.pop()            # 栈顶即中序的下一个节点
            # 与中序前驱比，不是与父节点比；等号不允许，所以用 >=
            if prev is not None and prev >= node.val:
                return False              # 中序出现非递增，立刻否掉
            prev = node.val
            cur = node.right              # 转向右子树
        return True
