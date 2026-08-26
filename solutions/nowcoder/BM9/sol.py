# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/f95dcdafbde44b22a6d741baf71653f6
# 判题: 核心代码模式
# 签名: removeNthFromEnd(head: ListNode、n: integer) -> ListNode

"""BM9 删除链表的倒数第n个节点 —— 哑节点 + 快慢指针拉开 n 的间距，一趟定位到待删节点的前驱。

这题考什么：
    单链表删节点靠的是改**前驱**的 next，所以真正要找的不是倒数第 n 个，
    而是倒数第 n+1 个。把「拉开固定间距的两个指针」当成一把尺子：
    让 fast 从哑节点先走 n 步，此后两者同步前进，间距恒为 n（这就是循环不变量）；
    fast 停在最后一个节点时，slow 正好落在待删节点的前一个，
    一句 `slow.next = slow.next.next` 就把目标摘掉了。

    哑节点（dummy head，值无意义、只为让表头也有前驱的辅助节点）在这题几乎是必需品：
    n 等于链表长度时删的就是表头，没有哑节点就得单写一个换头分支。
    链表的增删见 docs/ds/linked-list.md。

数据规模与复杂度：
    链表长度不超过 1000（题面里的 n 既指长度又指倒数序号），节点值在 [0, 100]，
    其他语言时限 2 秒，且题面保证 n 一定有效。
    一趟遍历 O(链表长度)、额外空间 O(1)，满足题面要求。
    先量长度再走一趟的两趟写法同阶也能过，快慢指针胜在只扫一遍，
    在「数据是流、只能读一次」的场景里是唯一可行的做法。

坑在哪：
  1. fast 必须从 **dummy** 而不是 head 出发。从 head 出发时两指针间距是 n-1，
     slow 会停在待删节点本身，拿不到前驱，删除就无从下手；
  2. 同步前进的条件是 `while fast.next`，让 fast 停在最后一个节点。
     写成 `while fast` 会让 fast 走到 None，slow 多前进一格，删掉的是倒数第 n-1 个；
  3. 待删的可能就是表头（n == 链表长度），所以结尾只能 `return dummy.next`；
     返回 head 时如果删的正是 head，交上去的还是那个被删掉的节点；
  4. 题面保证 n 有效，但拉间距的循环里仍然判了一次 `fast.next is None`：
     一旦输入越界，这个出口原样返回链表，而不是在 None 上取属性崩掉。

样例复核：
    {1,2}，n = 2。dummy->1->2。fast 从 dummy 走 2 步到节点 2，
    此时 slow 还在 dummy；fast.next 是 None，同步循环一次不进。
    slow.next = slow.next.next 把节点 1 摘掉，返回 dummy.next = 节点 2，
    输出 {2}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def removeNthFromEnd(self, head: "Optional[ListNode]", n: int) -> "Optional[ListNode]":
        dummy = ListNode(0)         # 哑节点：删的可能就是表头，必须让表头也有前驱
        dummy.next = head
        fast = slow = dummy         # 两者都从哑节点起步，间距才是 n 而不是 n-1
        for _ in range(n):          # 拉开 n 的间距
            if fast.next is None:   # 越界兜底：n 比链表还长，原样交回不崩
                return head
            fast = fast.next
        # 同步前进，间距恒为 n；fast 停在尾节点时 slow 正好是待删节点的前驱
        while fast.next:
            fast = fast.next
            slow = slow.next
        # slow 是待删节点的前驱：改它的 next 跨过目标，目标就此从链上脱钩
        slow.next = slow.next.next
        return dummy.next           # 表头可能已被删掉，只能从哑节点取
