# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/8b3b95850edb4115918ecebdf1b4d222
# 判题: 核心代码模式
# 签名: IsBalanced_Solution(pRoot: TreeNode) -> boolean

"""BM36 判断是不是平衡二叉树 —— 后序自底向上算高度，顺手检查每个节点的左右高度差。

这题考什么：
    平衡二叉树要求**每一个**节点的左右子树高度差不超过 1。照着定义写成
    「对每个节点各求一次左右子树高度」，高度会被反复重算：链状树上第 i 个
    节点的高度要被它上面 i 个祖先各算一遍，总代价 O(n^2)。

    省掉重复的关键是换方向：**自底向上**。后序遍历（左 -> 右 -> 根）保证
    轮到一个节点时它两棵子树都已处理完，于是一次遍历既算高度又做检查：

        h(node) = max(h(left), h(right)) + 1
        任何一个节点上 |h(left) - h(right)| > 1，整棵树立刻判负

    后序在这里必须是「真后序」，不能用 BM25 那种「根右左再整体逆序」的写法：
    那个技巧只能产出序列，给不出「站在某个节点上、两个孩子的结果都已备好」
    的时机。所以用**带展开标记的显式栈**：栈里存 (节点, 是否已展开)，
      - 弹出未展开的节点：先把 (node, True) 压回去，再压右孩子、左孩子，
        于是出栈顺序变成「左、右、根」；
      - 弹出已展开的节点：两个孩子的高度这时一定在表里了，比差值、
        再把自己的高度登记上去。

数据规模与复杂度：
    n <= 100，节点值满足 0 <= val <= 1000；时限「其他语言 2 秒」。
    每个节点入栈两次（展开前一次、展开后一次），高度只算一次，时间 O(n)；
    空间 O(n)，栈深等于树高，height 表存 n 个条目。
    题面「要求」一栏写的空间复杂度 O(1) 是理想指标，任何遍历写法都做不到。

坑在哪：
  1. **高度表的键必须是 id(node)，不能是节点值**。题面只约束 0 <= val <= 1000，
     并没有保证互不相同，n <= 100 的树里完全可以出现两个值相同的节点，
     用值当键会互相覆盖，高度全乱。这与 BM38 正相反：那题题面明确保证
     节点值互不相同，才可以拿 val 当键。
     用 id 是安全的：整棵树在函数返回前始终被调用方引用着，节点不会被回收，
     id 也就不会被别的对象复用。
  2. 展开时压栈的顺序不能变：先压回自己（标记为已展开），再压右、再压左。
     漏掉「先压回自己」就退化成普通前序，轮到根时孩子的高度还没算出来；
     左右压反则得到「右左根」，本题因为只比高度差的绝对值恰好看不出差别，
     但换成有序的后序任务就会错。
  3. 空子树的高度取 0，靠 `height.get(id(node.left), 0)` 的默认值给出。
     id(None) 从来不会被写进表里，所以这次 get 一定落到默认值上。
  4. 判否要在**每个**节点上做，不是只看根。只比根的左右高度差会漏掉
     深处的失衡；一旦某个节点超差就可以立即 return False，整棵树已无救。
  5. 空树按题面约定是平衡的（示例 2 直接给了 {}），返回 True。
  6. n <= 100 时递归不会爆栈，这里仍写迭代是为了与本专题统一：
     同一批的 BM28、BM38 的 n 到 1e5，那里递归版必然 RecursionError，
     一套模板贯穿全章，不必在两种范式之间来回切换。
"""
from typing import Dict, List, Optional


class Solution:
    def IsBalanced_Solution(self, pRoot: "Optional[TreeNode]") -> bool:
        # 空树按题面约定是平衡的
        if pRoot is None:
            return True
        height: Dict[int, int] = {}                     # id(node) -> 以它为根的高度
        stack = [(pRoot, False)]                        # (节点, 是否已展开)
        while stack:
            node, expanded = stack.pop()
            # 未展开：把自己压回去垫底，再压孩子，出栈顺序就成了「左 右 根」
            if not expanded:
                stack.append((node, True))              # 根留到孩子之后再处理
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
                continue
            # 已展开：两个孩子都处理完了，它们的高度一定已在表里
            lh = height.get(id(node.left), 0)           # 空子树高度为 0
            rh = height.get(id(node.right), 0)
            if abs(lh - rh) > 1:
                return False                            # 任一节点失衡即可收工
            height[id(node)] = max(lh, rh) + 1
        return True
