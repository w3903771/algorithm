# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/947f6eb80d944a84850b0538bf0ec3a5
# 判题: 核心代码模式
# 签名: Convert(pRootOfTree: TreeNode) -> TreeNode

"""BM30 二叉搜索树与双向链表 —— 中序遍历天然有序，遍历时顺手把前驱后继指针接上。

这题考什么：
    BST（二叉搜索树，左子树全部小于根、右子树全部大于根）的**中序遍历
    就是升序序列**，而题目要的双向链表恰好也是升序。两件事的顺序完全相同，
    所以整题归约成一句话：按中序访问节点，把相邻的两个接起来。

    接法由题面规定：复用 TreeNode 已有的两个字段，left 当前驱指针、
    right 当后继指针，不新建任何节点。做法是在迭代中序里多维护一个 prev
    表示「上一个被访问的节点」：
      - prev 为空说明当前节点是中序第一个，也就是最小值，记成链表头 head；
      - 否则 prev.right = cur、cur.left = prev，把两个方向都接上。
    然后 prev = cur，继续中序。

        示例 1 的 {10,6,14,4,8,12,16}，中序是 4, 6, 8, 10, 12, 14, 16，
        依次接成 4 <-> 6 <-> 8 <-> 10 <-> 12 <-> 14 <-> 16，返回 4。

数据规模与复杂度：
    0 <= n <= 1000，节点值满足 0 <= val <= 1000；时限「其他语言 2 秒」。
    中序遍历一趟，每个节点入栈出栈各一次，时间 O(n)；
    额外空间只有那个显式栈，O(h)，h 为树高，链状树退化到 O(n)。
    没有新建任何节点，符合题面「在原树上操作」的要求。

坑在哪：
  1. **改指针之前必须先把 cur.right 存下来**。这是本题最容易写错的一处：
     一旦执行 prev.right = cur，prev 原来的右子树就再也找不回来了；
     同理，弹出 cur、接完指针之后 cur.right 已经可能被下一步覆盖，
     所以中序的「转向右子树」必须用事先保存的 nxt，而不是现读 cur.right。
  2. **返回值不是一棵树，判题也不按树比**。这题由 driver.py
     驱动：驱动器拿到返回的 head 之后，先沿 right 正向走一遍收值，再找到尾
     节点沿 left 反向走一遍收值，拼成一整句话
         From left to right are:4,6,8,10,12,14,16;From right to left are:16,14,12,10,8,6,4;
     再和期望文本比。meta.json 的 judge 给它配的模式是 raw（不做方言解析、
     按原始文本比），因为这句话没有引号，按牛客方言解析会被顶层逗号切成列表，
     永远比不上。通用的树编码器在这里也用不了：它沿 left/right 做层序 BFS，
     而转换后的节点互相指回去，队列会无限膨胀直接跑到超时。
  3. 由第 2 条推出的实战后果：**两个方向都必须接对**。只写 prev.right = cur
     而漏掉 cur.left = prev，正向那半句仍然正确，反向那半句会立刻露馅——
     驱动器就是为了抓这种错法才两个方向都走。
  4. 链表头的 left 与链表尾的 right 都必须保持 None。这份写法天然满足：
     中序第一个节点没有左孩子、最后一个节点没有右孩子，代码不会去动它们。
     若额外接成环，驱动器的保险丝会截断遍历，答案自然对不上。
  5. 空树返回 None，驱动器对应输出两个空列表的那句话。
  6. n 可以取到 1000，而 CPython 的默认递归上限正是 1000 层：示例 2 的
     {5,4,#,3,#,2,#,1} 已经是一条纯左斜链，真数据里同样形状放大到 1000 个
     节点就会 RecursionError，所以中序写成显式栈。
"""
from typing import List, Optional


class Solution:
    def Convert(self, pRootOfTree: "Optional[TreeNode]") -> "Optional[TreeNode]":
        # 空树没有链表头，驱动器会输出两个空序列
        if pRootOfTree is None:
            return None
        head: "Optional[TreeNode]" = None   # 链表头 = 中序第一个 = 最小值
        prev: "Optional[TreeNode]" = None   # 上一个被访问的节点
        stack: List["TreeNode"] = []
        cur = pRootOfTree
        # 标准迭代中序：一路向左压栈 -> 弹出访问 -> 转向右子树
        while stack or cur is not None:
            while cur is not None:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            nxt = cur.right                 # 先存好右子树，下面要覆盖指针
            # 中序相邻的两个节点就是链表里相邻的两个，前后指针一起接
            if prev is None:
                head = cur                  # 中序的第一个节点就是链表头
            else:
                prev.right = cur            # 前驱 -> 后继
                cur.left = prev             # 后继 -> 前驱
            prev = cur
            cur = nxt                       # 用存下来的右子树继续中序
        return head
