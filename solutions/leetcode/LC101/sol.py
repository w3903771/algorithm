"""LC101 对称二叉树 —— 把「整棵树轴对称」化成「左右两棵子树互为镜像」，成对地比。

这题考什么：
    轴对称说的是把树沿根节点竖直翻折后能重合。对整棵树直接下判断没有抓手，
    要换成一个能往下递推的命题：**root.left 与 root.right 互为镜像**。

    两棵树 a、b 互为镜像的充要条件是三条同时成立：
        a 与 b 同时为空，或者同时非空；
        a.val == b.val；
        a.left 与 b.right 互为镜像，且 a.right 与 b.left 互为镜像。

    第三条是全部关键：镜像要**交叉**配对，左配右、右配左。
    若写成 a.left 配 b.left，比的就变成了「两棵树完全相同」，
    示例 1 的 [1,2,2,3,4,4,3] 会被判否 —— 它的左子树读作 (2,3,4)、
    右子树读作 (2,4,3)，相同性不成立，镜像性才成立。

    实现用显式栈成对处理：栈里放「还没比过的节点对」，弹出一对比一对，
    合格就把两组交叉孩子再压回去。

数据规模与复杂度：
    节点数在 [1, 1000]，节点值在 [-100, 100]。
    每个节点最多参与一对比较，时间 O(n)；栈里同时存在的节点对不超过树高，
    空间 O(h)，链状树退化到 O(n)。
    n = 1000 时链状树的递归深度恰好顶到 CPython 默认的 1000 层上限，
    本来就在会不会炸的边界上，写成显式栈就不必赌；
    递归改迭代见 docs/search/dfs.md 的 60.4 节。

坑在哪：
  1. **必须交叉配对**：a.left 对 b.right、a.right 对 b.left。写成同侧配对
     就成了判断两棵子树相等，示例 1 会被直接判错。
  2. **「一个空一个非空」要单独判掉**。只比 a.val != b.val 的话，
     示例 2 的 [1,2,2,null,3,null,3] 会在一侧为空时对 None 取 .val，
     抛 AttributeError 而不是返回 False。这一条判的是结构，前一条判的是值，
     两者都不能省。
  3. 题面写 n >= 1，但题面的边界描述从来不是担保。这份写法对空树也安全：
     开头一句挡住 root 为 None，返回 True，与「空树对称」的通常约定一致。
  4. 发现一对不匹配立刻返回 False。对称性是所有节点对同时成立的合取，
     一对出局就再也救不回来，这是合法的提前退出。
"""
from typing import List, Optional


class Solution:
    def isSymmetric(self, root: "Optional[TreeNode]") -> bool:
        # 空树无从翻折，按「空树对称」处理；这一句也保证下面能安全取 root.left
        if root is None:
            return True
        # 栈里是「还没比过的节点对」，初始只有根的左右子树这一对
        stack = [(root.left, root.right)]
        while stack:
            a, b = stack.pop()
            # 两侧同时到头，这一支的镜像成立，换下一对
            if a is None and b is None:
                continue
            # 只有一侧到头 -> 结构就不对称；先判掉才能安全取下面的 .val
            if a is None or b is None:
                return False
            # 值不等立刻出局：对称是所有节点对同时成立，一对错了整棵树就废
            if a.val != b.val:
                return False
            # 交叉配对才是镜像：a 的左对 b 的右，a 的右对 b 的左
            stack.append((a.left, b.right))
            stack.append((a.right, b.left))
        # 所有节点对都通过了检查
        return True
