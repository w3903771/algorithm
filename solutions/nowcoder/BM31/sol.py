# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/ff05d44dfdb04e1d83bdbdab320efbcb
# 判题: 核心代码模式
# 签名: isSymmetrical(pRoot: TreeNode) -> boolean

"""BM31 对称的二叉树 —— 用一个栈同时推进两条镜像路径，成对比较左右子树。

这题考什么：
    「是自身的镜像」不等于「左子树等于右子树」，而是**左子树等于右子树的镜像**。
    把它写成两棵树之间的判定 same(a, b)，四条规则就穷尽了所有情况：

        a、b 都空      -> 这一支对称
        只有一个空     -> 形状不同，不对称
        值不相等       -> 不对称
        否则           -> 递归比较 (a.left, b.right) 与 (a.right, b.left)

    整棵树对称当且仅当 same(root.left, root.right)。

    最后一行的**交叉配对**是全题的要点：镜像意味着 a 的外侧要对上 b 的外侧，
    而 a 的外侧是左、b 的外侧是右。示例 1 的 {1,2,2,3,4,4,3} 正好演示：
    左子树 2 的孩子是 (3, 4)，右子树 2 的孩子是 (4, 3)，交叉着比是
    3 对 3、4 对 4，判 true；若按同侧比就成了 3 对 4，会把一棵对称树判成 false。
    反过来 {1,2,2,3,4,3,4} 两边孩子都是 (3, 4)，同侧比会误判成 true，
    交叉比才看出 3 与 4 对不上——它确实不是对称树。

    实现把递归换成显式栈：栈里成对存 (a, b)，弹出一对按四条规则判，
    需要继续比的两对再压回去。栈里允许出现 None——「一边空一边不空」
    正是判否的依据，把 None 过滤掉就等于丢掉了形状信息。

数据规模与复杂度：
    0 <= n <= 1000，节点值满足 |val| <= 1000；时限「其他语言 2 秒」。
    每个节点最多参与一次配对，时间 O(n)；空间 O(n)，栈里存待比较的节点对。

坑在哪：
  1. 交叉配对不能写成同侧配对。写成 (a.left, b.left) 判的是「两棵树相同」，
     跟对称是两回事，见上面两个互为反证的例子。
  2. 四条规则的**先后顺序**不能换：必须先判「两个都空」再判「只有一个空」。
     顺序颠倒的话，两个都空会先落进「只有一个空」的分支被判 False，
     每一条到底的分支都会误判。
  3. 光比值不比形状不行。a 有左孩子、b 没有，两个节点的 val 却相等，
     只有那条「一空一不空 -> False」的规则能拦住。
  4. 空树按题意是对称的，返回 True；起手直接比 (root.left, root.right)，
     所以根节点自身的值从不参与比较——对称性本来也不约束根。
  5. n 可以取到 1000，而 CPython 的默认递归上限正是 1000 层，链状树的
     递归深度就是 n，加上判题驱动本身占掉的几层足以 RecursionError，
     所以写成显式栈；三层限制见 docs/search/dfs.md 的 60.4 节。
"""
from typing import List, Optional, Tuple


class Solution:
    def isSymmetrical(self, pRoot: "Optional[TreeNode]") -> bool:
        # 空树视为对称；非空时对称性只约束根的两棵子树，根自身的值不参与比较
        if pRoot is None:
            return True
        stack = [(pRoot.left, pRoot.right)]     # 待比较的镜像节点对
        while stack:
            a, b = stack.pop()
            # 四条规则的顺序不能换：先判「两个都空」，再判「只有一个空」
            if a is None and b is None:
                continue                        # 两边同时到头，这一支合格
            if a is None or b is None:
                return False                    # 一边到头一边没有，形状就不对称
            if a.val != b.val:
                return False
            # 镜像 = 外侧对外侧、内侧对内侧，所以两对都要交叉着压回去
            stack.append((a.left, b.right))     # 交叉配对：外侧对外侧
            stack.append((a.right, b.left))     # 内侧对内侧
        return True
