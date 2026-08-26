"""LC19 删除链表的倒数第 N 个结点 —— 一趟扫描删掉从后往前数第 n 个节点，返回新表头。

这题考什么：
    链表只能从头往后走，「倒数第 n 个」没法直接定位。把它翻译成可走的语言：
    倒数第 n 个节点，就是「距离链尾还差 n - 1 步」的那个节点。

    双指针（也叫快慢指针）把这个距离固化成两个指针之间的**固定间隔**：
    让 fast 先走若干步，再让 fast 与 slow 同速前进，fast 撞到链尾时，
    slow 自然停在想要的位置。间隔一旦拉开就永远不变，这就是循环不变量。

    要删除一个节点，手上必须握着它的**前驱**（改的是前驱的 next）。
    所以间隔取 n + 1：fast 从哨兵出发先走 n + 1 步，此后 fast 每前进一步 slow 也进一步，
    fast 变成 None 时 slow 恰好停在待删节点的前一个。

    哨兵（dummy）节点在这里不只是简化：删除的可能就是头节点本身（n == sz），
    这时「前驱」在原链里根本不存在，哨兵把它补出来了。
    链表与哨兵的用法见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数 sz 最多 30，且题面保证 1 <= n <= sz，不会出现越界的 n。
    一趟扫描 O(sz) 时间、O(1) 额外空间，完全满足进阶要求。
    先遍历一遍数长度、再走 sz - n 步的两趟写法同样是 O(sz)，
    但要多一次完整遍历；在只能单向流式读取的场景（如超大文件的链式记录）里，
    两趟写法根本没法用，双指针才是通用解。

坑在哪：
  1. fast 必须从**哨兵**出发走 n + 1 步，而不是从 head 走 n 步。
     少走这一步，slow 会停在待删节点自己身上，拿不到前驱就改不了链；
  2. 不加哨兵时 n == sz（删头节点）会崩：slow 停在 None 上，`slow.next` 直接
     AttributeError。样例二 [1] 删倒数第 1 个正是这种情况，期望输出是空链 []；
  3. 前进 n + 1 步不会走过头。链上连哨兵共 sz + 1 个节点，n <= sz 保证
     n + 1 <= sz + 1，最远也只是让 fast 落在最后一个节点上；
  4. 返回值取 dummy.next 不是 head。删的若是头节点，head 已经是被摘掉的那个，
     返回它等于什么都没删。

样例复核：
    [1,2,3,4,5]、n = 2。dummy -> 1 -> 2 -> 3 -> 4 -> 5。
    fast 先走 3 步落在节点 3。同步前进：fast = 4 / slow = 1，fast = 5 / slow = 2，
    fast = None / slow = 3。删 slow.next 即节点 4，得 [1,2,3,5]，与样例一致。
"""
from typing import List, Optional


class Solution:
    def removeNthFromEnd(self, head: "Optional[ListNode]", n: int) -> "Optional[ListNode]":
        # 哨兵挂在真表头前面：删头节点时它就是那个「不存在的前驱」
        dummy = ListNode(0)
        dummy.next = head
        fast = dummy
        slow = dummy
        # 先把间隔拉到 n + 1：多的这一步是为了让 slow 最终停在待删节点的**前驱**上
        for _ in range(n + 1):
            fast = fast.next
        # 间隔固定不变，fast 走到 None 时 slow 距链尾恰好还有 n 个节点
        while fast:
            fast = fast.next
            slow = slow.next
        # slow.next 就是倒数第 n 个，跨过它即完成删除
        slow.next = slow.next.next
        return dummy.next                # 头节点可能已被删掉，只能从哨兵取新表头
