# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/a9d0ecbacef9410ca97463e4a5c83be7
# 判题: 核心代码模式
# 签名: Mirror(pRoot: TreeNode) -> TreeNode

"""BM33 二叉树的镜像 —— 遍历每个节点，把它的左右孩子对调一次即可。

这题考什么：
    镜像的含义是「每个节点的左右子树互换」。关键观察是这件事对各个节点
    **互相独立**：交换的只是两个指针，被交换的子树内部结构一点没动，
    所以先换父节点还是先换子节点都得到同一个结果，遍历顺序完全自由。

    既然顺序无所谓，就用最省事的显式栈遍历：
      1. 栈里放根；
      2. 弹出一个节点，用元组赋值一次性对调它的两个孩子；
      3. 把对调后非空的两个孩子压回栈——对调前后压进去的是同一批节点，
         只是左右换了名字，压的顺序也就无关紧要；
      4. 栈空即结束，返回原来的根。

        示例 1 的 {8,6,10,5,7,9,11}：8 的两个孩子换成 (10, 6)，
        10 的孩子换成 (11, 9)，6 的孩子换成 (7, 5)，
        结果 {8,10,6,11,9,7,5}，与样例输出一致。

数据规模与复杂度：
    0 <= n <= 1000，节点值满足 0 <= val <= 1000；时限「其他语言 2 秒」。
    每个节点恰好对调一次，时间 O(n)；空间 O(h)，h 为树高，链状树退化到 O(n)。
    原地改指针、不新建节点，符合题面「本题也有 O(1) 空间原地解法」的方向。

坑在哪：
  1. 对调必须写成元组同时赋值。拆成两条语句
         node.left = node.right
         node.right = node.left
     第二条读到的已经是刚被覆盖过的 node.left，结果是两侧都变成原来的右子树，
     整棵左子树凭空丢失。Python 的元组赋值先把右侧两个值一次算完，天然没这问题。
  2. 每个节点都要换，且只换一次。漏掉任何一个节点，那一段子树保持原样；
     若在同一个节点上换两次（例如既在弹出时换、又在压栈时换），等于没换。
  3. 返回的是**原来的根**：这是原地改造，不是造一棵新树。返回值写成 None
     或新建的节点都会判错。
  4. 空树是合法输入，返回 None，判题期望 {}（示例 2 就给了 {}）。
     少了空树守卫，栈里会被塞进一个 None，下一轮取 node.left 就 AttributeError。
  5. n 可以取到 1000，恰好是 CPython 的默认递归上限，链状树的递归深度就是 n，
     所以统一写成显式栈；三层限制见 docs/search/dfs.md 的 60.4 节。
"""
from typing import List, Optional


class Solution:
    def Mirror(self, pRoot: "Optional[TreeNode]") -> "Optional[TreeNode]":
        # 空树返回 None（判题期望 {}），同时保证栈里全是真节点
        if pRoot is None:
            return None
        stack = [pRoot]
        while stack:
            node = stack.pop()
            # 元组同时赋值：右侧两个值先算完再写回，拆成两条语句会丢掉左子树
            node.left, node.right = node.right, node.left   # 就地对调
            # 交换只动指针、不动子树内部，所以压栈顺序与结果无关
            if node.left is not None:
                stack.append(node.left)
            if node.right is not None:
                stack.append(node.right)
        return pRoot
