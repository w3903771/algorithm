# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/71cef9f8b5564579bf7ed93fbe0b2024
# 判题: 核心代码模式
# 签名: deleteDuplicates(head: ListNode) -> ListNode

"""BM16 删除有序链表中重复的元素-II —— 哑节点守门，一旦发现重复就把整组同值节点全跳过。

这题考什么：
    和 BM15 只差一个字：重复出现的值**一个都不留**（1,2,2 变成 1；1,1,2,2 变成空表）。
    这一个字带来两处结构性变化：

      1. **表头可能被删光**，所以必须上哑节点（dummy head，值无意义、
         只为让表头也有前驱的辅助节点），最后 `return dummy.next` 兜住换头；
      2. 判断要看 pre 之后的**两个**节点：`pre.next.val == pre.next.next.val`
         说明这个值有重复，于是记下它，用一个内层循环把所有等于它的节点一路跳过，
         再把 pre.next 接到第一个不等于它的节点上。

    删除发生时 pre **不前移**：它后面新接上的节点还没和自己的后继比过。
    没有重复时 pre 正常前移一格。pre 的不变量是「pre 及其之前都已确认保留」。
    链表的删除见 docs/ds/linked-list.md。

数据规模与复杂度：
    链表长度 0 <= n <= 10000，|val| <= 1000，其他语言时限 2 秒。
    每个节点只被内外两层循环之一访问一次，时间 O(n)、额外空间 O(1)，
    达到题面进阶要求。虽然有嵌套循环，内层跳过的节点不会再被外层碰到，
    所以总步数是 n 而不是 n 的平方。
    另一条思路是先统计每个值出现几次再重建链表，时间同阶但要 O(n) 空间，
    并且同样依赖有序才能一趟统计。

坑在哪：
  1. 表头可能整组被删（如 1,1,2,2 的答案是空表），必须用哑节点，
     且只能 `return dummy.next`。返回 head 时若 head 正属于被删的那一组，
     交上去的是一个已经被跳过的节点；
  2. 删除之后 pre 不能前移。前移会跳过「新接上来的节点是否也重复」这一次检查，
     1,1,2,2 会剩下 2；
  3. 内层循环必须先判空再取 val（`while cur and cur.val == v`）：
     重复段可能一直延伸到表尾（如 1,1,1），先取 val 会在 None 上崩；
  4. 外层条件是 `while pre.next and pre.next.next`，要看到两个节点才谈得上比较；
     剩下不足两个节点时它们必然互不重复，循环结束正好收工；
  5. 重复值要先存进 v 再开始跳。直接拿 `pre.next.val` 当基准，
     pre.next 在循环里被改掉后基准也跟着变，跳过的范围就错了。

样例复核：
    {1,2,2}：pre = dummy，pre.next = 1、pre.next.next = 2，两者不等，pre 前移到 1；
    此时 pre.next = 2、pre.next.next = 2 相等，记下 v = 2，
    内层从第一个 2 一路跳到 None，pre.next = None。
    外层条件不再成立，返回 dummy.next 得 {1}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def deleteDuplicates(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        dummy = ListNode(0)         # 表头可能整组被删，必须有哑节点兜住换头
        dummy.next = head
        pre = dummy                 # 不变量：pre 及其之前的节点都已确认保留
        # 要比较的是 pre 后面的两个节点，不足两个就没有重复可言，收工
        while pre.next and pre.next.next:
            # 相邻两个同值即说明这个值有重复，按题意整组删光，一个都不留
            if pre.next.val == pre.next.next.val:
                v = pre.next.val    # 先存基准值：pre.next 马上要被改，不能现取现比
                cur = pre.next
                while cur and cur.val == v:     # 先判空：重复段可能一直延伸到表尾
                    cur = cur.next
                pre.next = cur      # 整组跳过；pre 不动，新接上的节点还没查过
            else:
                pre = pre.next      # 确认这一格不重复才前移
        return dummy.next
