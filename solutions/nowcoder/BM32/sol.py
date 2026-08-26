# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/7298353c24cc42e3bd5f0e0bd3d1d759
# 判题: 核心代码模式
# 签名: mergeTrees(t1: TreeNode、t2: TreeNode) -> TreeNode

"""BM32 合并二叉树 —— 同步走两棵树，都在就把值加到 t1 上，只剩一棵就整棵挂过去。

这题考什么：
    合并规则只有两条：同一个位置上两边都有节点就把值相加，只有一边有就直接
    用那一边的节点。第二条是效率的关键——「只有一边有」意味着另一边整片
    子树都是空的，把那棵子树**整体挂过来**和逐个节点复制的结果完全一样，
    但省掉了对它的全部下探。

    于是只有「两边都非空」的位置才需要继续处理，把这些位置成对放进栈：
      1. t1 为空返回 t2、t2 为空返回 t1（顺带覆盖了两棵都空的情况）；
      2. 栈里成对存两边都非空的节点 (a, b)，初始是 (t1, t2)；
      3. 弹出一对，先 a.val += b.val，再分左右孩子讨论：
           两边都有孩子 -> 压回栈，留待下一轮；
           只有 b 有     -> a 的这一侧直接指向 b 的整棵子树，不再下探；
           只有 a 有     -> 什么都不做，保持原样；
      4. 返回 t1。

    答案直接长在 t1 上，全程不新建节点。

        示例 1 的 {1,3,2,5} 与 {2,1,3,#,4,#,7}：
        根 1+2 = 3；左 3+1 = 4；右 2+3 = 5；t1 的 5 那一侧 t2 没有，原样保留；
        t2 在 4、7 两处 t1 没有，整枝挂过来。结果 {3,4,5,5,4,#,7}，与样例一致。

数据规模与复杂度：
    0 <= n <= 500，节点值在 32 位整型范围内；时限「其他语言 2 秒」。
    循环只走两树的重叠部分，时间与空间都是 O(min(n1, n2))；
    非重叠部分靠指针整体挂接，是 O(1) 的操作。

坑在哪：
  1. 「只有 a 有孩子」的分支必须**什么都不做**。写成 else 一把兜底
     （`else: a.left = b.left`）会在 b.left 为 None 时把 a 原有的整棵左子树
     置空，示例 1 里 t1 的节点 5 就会凭空消失。
  2. 栈里只放「两边都非空」的配对，这是循环不变量，所以循环体开头可以
     放心地直接 a.val += b.val 而不必再判空。往栈里塞过 None，这一行立刻炸。
  3. 「只有一边有」时不要再往下递归复制。逐点复制答案不错，但把 O(1) 的
     挂接变成 O(子树大小) 的遍历，也失去了「原地合并、不新建节点」的性质。
  4. 结果原地长在 t1 上，调用方看到的 t1 已经被改写。题面允许这样做
     （进阶要求就是空间 O(1)），但这意味着传进来的两棵树都不能再当原样使用。
  5. 空树参与合并是合法输入：示例 2 的 {1} 与 {} 期望 {1}，靠开头那两行守卫
     处理；两棵都空时第一行返回 t2，也就是 None。
  6. 值域是 32 位整型，两两相加会越过 32 位——Python 的整数是任意精度，
     这里不会溢出，用 C++ / Java 写同一题才需要换宽类型。
"""
from typing import List, Optional


class Solution:
    def mergeTrees(self, t1: "Optional[TreeNode]", t2: "Optional[TreeNode]") -> "Optional[TreeNode]":
        # 有一棵为空就直接返回另一棵；两棵都空时返回的就是 None
        if t1 is None:
            return t2
        if t2 is None:
            return t1
        # 循环不变量：栈里的每一对左右都非空，所以循环体里不必再判空
        stack = [(t1, t2)]                       # 栈里只放两边都非空的配对
        while stack:
            a, b = stack.pop()
            a.val += b.val                       # 不变量保证 a、b 都不是 None
            # 三种情况：都在则继续下探；只有 t2 有则整枝挂接；只有 t1 有则原样不动
            if a.left is not None and b.left is not None:
                stack.append((a.left, b.left))   # 都在，继续往下合
            elif b.left is not None:
                a.left = b.left                  # 只有 t2 有，整棵子树挂过来
            if a.right is not None and b.right is not None:
                stack.append((a.right, b.right))
            elif b.right is not None:
                a.right = b.right
        return t1
