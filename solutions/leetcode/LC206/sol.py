"""LC206 反转链表 —— 把每条 next 边掉头，原来的尾节点成为新表头。

这题考什么：
    反转链表改的是**边的方向**，节点对象一个都不用新建、val 一个都不用动。
    维护两个指针：prev 指向已经反转好的那一段的头，cur 指向还没处理的那一段的头。
    每轮把 cur 这条边掉头，然后两个指针一起前移。

    循环不变量：prev 那段已经全部反转完毕、cur 那段仍是原顺序，两段没有交集，
    并且 prev 段的尾巴（即原表头）的 next 恒为 None。
    cur 走到 None 时未处理段为空，prev 正停在原链的最后一个节点上，就是答案。

    每轮四步的顺序是死的：先用 nxt 存住后路，再改 cur.next，最后推进两个指针。
    链表的结构与指针搬移见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数最多 5000，值域 -5000..5000。迭代版一趟遍历 O(n) 时间、O(1) 额外空间，
    最坏五千次指针赋值，毫无压力。

    进阶提到的递归写法（先递归反转 head.next 之后的部分，再把 head 接到尾部）
    时间同样 O(n)，但递归深度等于节点数。n 上限 5000 已经**超过 Python 默认的
    1000 层递归上限**，直接提交会 RecursionError；要用递归就得先调
    sys.setrecursionlimit，属于给自己找麻烦。迭代版没有这个问题。

    还有一种做法是把所有 val 收进列表再倒序建链，时间 O(n) 但要多开 O(n) 空间、
    多造 n 个节点对象，不满足常数空间的要求。

坑在哪：
  1. `nxt = cur.next` 必须写在 `cur.next = prev` **之前**。顺序反过来，
     cur.next 已经被改成 prev，nxt 拿到的是前驱，两个节点来回打转，
     while 永远走不到 None，死循环；
  2. 返回 prev 不是 cur。循环退出时 cur 已经是 None，返回它等于交了个空链表；
  3. prev 起手必须是 None。它同时充当「原表头反转后的新尾巴」的终止标记，
     写成别的值会让新链尾巴挂着一段旧数据，遍历不到头；
  4. 空链与单节点不用特判：head 为 None 时 while 一次都不进，返回 None，
     正对应样例三期望的空链 []；单节点进一次循环，next 被置成 None 后原样返回。

样例复核：
    [1,2]。第一轮 nxt = 2，1.next = None，prev = 1，cur = 2；
    第二轮 nxt = None，2.next = 1，prev = 2，cur = None，退出。
    返回 prev = 2，整条链是 2 -> 1，与样例二一致。
"""
from typing import List, Optional


class Solution:
    def reverseList(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # prev 起手取 None：它既是「已反转段的头」，也是新链尾节点的终止标记
        prev = None
        cur = head
        # cur 走到 None 表示原链的每条边都已经掉过头
        while cur:
            nxt = cur.next       # 先存后路：下一句会把 cur.next 覆盖掉
            cur.next = prev      # 掉头，这条边从「指向后继」变成「指向前驱」
            prev = cur           # 已反转段前移，cur 成为新的段头
            cur = nxt            # 未处理段前移
        return prev              # 退出时 prev 停在原链尾节点，也就是新表头
