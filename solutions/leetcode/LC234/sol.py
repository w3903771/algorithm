"""LC234 回文链表 —— 判断链表正着读和反着读是不是同一串值。

这题考什么：
    数组判回文只要首尾两个下标往中间夹，但单链表没有「前一个」这种操作，
    右指针没法往左走。破局办法是**把后半段就地反转**，让它的遍历方向变成从尾向头，
    于是两段可以同时从各自的起点往前走，逐位比较。

    三步：
      1. 快慢指针找中点。fast 一次两步、slow 一次一步，fast 走完时 slow 落在
         后半段的起点（偶数长度落在右半段第一个，奇数长度落在正中间那个）；
      2. 从 slow 开始原地反转，得到一条从原尾节点回头走的链，头是 prev；
      3. 一个指针从原表头出发、一个从 prev 出发，逐位比 val，
         比到后半段走完为止。

    第三步只需要走到**后半段**走完，因为两段长度相差最多 1；奇数长度时
    正中间那个节点会和自己比一次，恒相等，不影响结论。
    链表与快慢指针见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数最多 10^5，val 只取 0..9。找中点 O(n)、反转 O(n)、比较 O(n)，
    合计 O(n) 时间；只用了几个指针，额外空间 O(1)，正是进阶要求的组合。

    最直白的做法是把 val 全收进列表再比 `vals == vals[::-1]`，时间同样 O(n)，
    但要存 10^5 个值，空间 O(n)，不满足进阶。另一种「递归到底再回溯着比」的写法
    空间看着像 O(1)，实际递归深度等于节点数：10^5 层远超 Python 默认的 1000 层上限，
    一提交就是 RecursionError。

坑在哪：
  1. 反转必须从 slow 开始，不能从 slow.next 开始。偶数长度时 slow 已经是右半段
     的第一个节点，从 slow.next 起手会漏掉一个，比较时两段长度对不上；
  2. 比较的循环条件挂在**右指针**上（`while right`），不能挂在左指针上。
     反转后前半段的最后一个节点仍指向反转段内部，左指针不会自己停下来；
  3. 这个解法会**改坏输入链表**：后半段被反转后原链不再完整。力扣的判题只看
     返回的布尔值，不检查链表，所以能过；但若函数的调用方之后还要用这条链，
     必须在返回前再把后半段反转回去；
  4. 比的是 val 不是节点身份。回文判断关心的是值序列，这里与 LC141 判环
     必须用 `is` 的要求正好相反，两题别串。

样例复核：
    [1,2,2,1]。找中点：slow 停在下标 2（第二个 2）。反转后半段得到 1 -> 2（从原尾回头）。
    比较：左 1 对右 1，左 2 对右 2，右侧走完，返回 True。
    [1,2]：slow 停在下标 1，反转后 prev 就是值 2 的节点，左 1 对右 2 不等，
    返回 False，与样例二一致。
"""
from typing import List, Optional


class Solution:
    def isPalindrome(self, head: "Optional[ListNode]") -> bool:
        # 第一步：快慢指针找后半段起点。fast 走两倍路程，它到头时 slow 正好过半
        slow = head
        fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        # 第二步：从 slow 起就地反转，prev 最终指向原链尾节点，成为「倒着走」的表头
        prev = None
        cur = slow
        while cur:
            nxt = cur.next       # 先存后路，下一句会覆盖 cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # 第三步：左段从原表头正着走，右段从原尾节点倒着走，逐位比值
        left = head
        right = prev
        # 条件挂在 right 上：左段末尾仍连着反转后的段，left 不会自己停下来
        while right:
            if left.val != right.val:
                return False     # 出现一对不相等，整条链就不是回文，可以立刻收工
            left = left.next
            right = right.next
        return True
