# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/1291064f4d5d4bdeaefbf0dd47d78541
# 判题: 核心代码模式
# 签名: postorderTraversal(root: TreeNode) -> integer[]

"""BM25 二叉树的后序遍历 —— 按「根 右 左」跑一遍前序变体，最后整体逆序。

这题考什么：
    后序（postorder）是「左 -> 右 -> 根」，根排在最后。直接迭代最麻烦：
    从右子树回到父节点时，栈顶那个父节点到底是「刚展开完左子树」还是
    「左右都完了」，光看节点本身分不出来，得额外记一位状态。

    绕开状态位的办法是从结果的对称性入手。把前序模板的压栈顺序调换
    （先压左、后压右），出栈序列就从「根 左 右」变成「根 右 左」；
    而「根 右 左」整体倒过来正是「左 右 根」——就是后序。

        前序模板   根 左 右
        镜像一下   根 右 左      （压栈改成先左后右）
        整体逆序   左 右 根      = 后序

        示例 1 的 {1,#,2,3}：根 1，右孩子 2，2 的左孩子 3。
        「根 右 左」序列是 1, 2, 3；逆序得 3, 2, 1，与样例输出一致。

    代价是必须先把整个序列生成完才能逆序，所以这是「离线」的写法：
    它给不出「访问到第 k 个节点时」的中间状态。需要在节点处真正做事、
    且必须等两个孩子都算完（比如 BM36 自底向上求高度），就得改用带
    展开标记的两趟栈。模板对照见 docs/graph/tree/basic.md 的「二叉树的三种遍历」一节。

数据规模与复杂度：
    n <= 100，节点值在 [1, 100] 且互不相同；时限「其他语言 2 秒」。
    每个节点入栈出栈各一次，末尾逆序一次，时间 O(n)；
    空间 O(n)，结果数组占 n，栈最深是树高。

坑在哪：
  1. 压栈顺序与前序**正好相反**：这里先压左、后压右。照抄前序的「先右后左」
     再逆序，得到的是「右 左 根」，左右子树整段对调，全错。
  2. 逆序要在最后**整体**做一次。写成边遍历边 `out.insert(0, node.val)`
     结果一样，但 list.insert(0, x) 要把已有元素整体后移，n 次就是 O(n^2)，
     而 list.reverse() 是一次 O(n) 的原地翻转。
  3. `out.reverse()` 原地翻转并返回 None，所以必须先 reverse 再单独 return。
     写成 `return out.reverse()` 交上去是一个 null，判题直接判错。
  4. 空树守卫不能省：少了它 stack 会被塞进一个 None，下一轮 `node.val`
     抛 AttributeError。本题题面写 n >= 1，但同专题的 BM24、BM33 都实测有 {}
     用例，题面的边界描述从来不是担保。
"""
from typing import List, Optional


class Solution:
    def postorderTraversal(self, root: "Optional[TreeNode]") -> List[int]:
        # 空树返回空列表，同时保证下面栈里全是真节点
        if root is None:
            return []
        out: List[int] = []
        stack = [root]
        # 这一趟跑的是前序的镜像，得到的是「根 右 左」而不是后序
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.left is not None:
                stack.append(node.left)   # 左先压 -> 后出
            if node.right is not None:
                stack.append(node.right)  # 右后压 -> 先出，得到「根 右 左」
        # 原地翻转：O(n) 一次，比逐个 insert(0, x) 的 O(n^2) 便宜
        out.reverse()                     # 「根 右 左」逆序 = 「左 右 根」
        return out
