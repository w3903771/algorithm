# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/253d2c59ec3e4bc68da16833f79a38e4
# 判题: 核心代码模式
# 签名: EntryNodeOfLoop(pHead: ListNode) -> ListNode

"""BM7 链表中环的入口结点 —— 快慢指针先相遇，再让一个指针从表头同速走，碰头处即入口。

这题考什么：
    第一步和 BM6 一样，用 Floyd 判圈的快慢指针确认有没有环，没环直接返回 None。
    第二步是这个算法真正值钱的地方，把式子推一遍就明白为什么不用求环长：

    设表头到入口的距离为 a，入口到相遇点的距离为 b，相遇点再回到入口的距离为 c
    （于是环长 = b + c）。相遇时 slow 走了 a + b，fast 走了 a + b + k(b + c)
    （在环里多绕了 k 圈），又 fast 的路程是 slow 的两倍：

        2(a + b) = a + b + k(b + c)   =>   a = k(b + c) - b = (k-1)(b+c) + c

    右边读作「从相遇点出发，绕 k-1 整圈再走 c 步」，落点正是入口。
    所以让 p 从表头、slow 从相遇点**同速各走一步**，两者必然在入口处碰头，
    与 k 是几无关，也不必先量环长。双指针技巧见 docs/basic/two-pointer.md。

数据规模与复杂度：
    n <= 10000，结点值在 [1, 10000]，其他语言时限 2 秒。
    第一步不超过 2n 步，第二步不超过 n 步，时间 O(n)、额外空间 O(1)。
    哈希表法（边走边记节点，第一个重复出现的就是入口）代码更短，
    但要 O(n) 空间，不满足题面的空间复杂度 O(1)。

坑在哪：
  1. **本题的输入是两段**：`{1,2},{3,4,5}`，前段是入环前的直链，后段是环本身。
     后台把后段首尾相接成环、再挂到前段末尾，函数签名里只有一个 pHead，
     看不出这回事；第二段为空就表示无环。本仓库的复现见 driver.py，
     自己造测试数据时必须照这个约定接环，否则永远只测到无环分支；
  2. 期望输出是入口结点的**值**（样例一是 3），无环时打印 "null"。
     题解返回的是结点本身，由后台取值打印，别自作主张返回数字；
  3. 相遇点在环内的某处，**不是入口**。b 只有在 a 恰好是环长整数倍时才等于 0，
     直接把相遇点当答案交上去，样例一会返回 4 或 5；
  4. 第二步的循环是 `while p is not slow` 先判后走：a == 0（表头就是入口）时
     一步都不走，直接返回 pHead，先走再判会整整多绕一圈；
  5. 无环时 fast 会撞到链尾，函数返回 None，对应样例二的 "null"。

样例复核：
    {1,2},{3,4,5}：整条链是 1->2->3->4->5->3，入口是 3，a = 2，环长 3。
    slow 依次走到 2、3、4，fast 依次走到 3、5、4，第 3 轮同时落在 4，
    于是 b = 1、c = 2。
    再让 p 从 1、slow 从 4 同速走两步：p 到 3，slow 走 5->3，两者在 3 相遇，
    返回值为 3 的结点，与样例一致。
"""
from typing import List, Optional


class Solution:
    def EntryNodeOfLoop(self, pHead: "Optional[ListNode]") -> "Optional[ListNode]":
        # 第一步：Floyd 判圈。fast 每轮两步，条件里两个非空判断缺一不可
        slow = fast = pHead
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                # 第二步：由 a = (k-1)(b+c) + c，从表头和从相遇点同速走必在入口相会。
                # 循环先判后走，入口就是表头（a = 0）时一步都不走，直接返回 pHead
                p = pHead
                while p is not slow:
                    p = p.next
                    slow = slow.next
                return p
        return None                 # fast 跑到链尾，无环，后台会把 None 打印成 "null"
