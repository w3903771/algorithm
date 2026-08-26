"""LC141 环形链表 —— 判断单链表里有没有环，有环则从某点出发能无限走下去。

这题考什么：
    Floyd 判圈算法（又叫龟兔赛跑算法，用两个速度不同的指针检测环）。
    slow 每轮走一步、fast 每轮走两步：

    - 没有环时，链是有限长的一条直线，fast 迟早撞到链尾的 None，循环退出；
    - 有环时两个指针都会进环并永远出不来。进环之后看它们的**间距**：
      每轮 fast 比 slow 多走一步，间距就减少 1，减到 0 就是相遇。
      间距是环长以内的非负整数，最多经过环长轮必然归零，所以一定会相遇，
      不存在「快的从慢的头上跳过去」的情况——每轮只多迈一步，跨不过去。

    这就是全题的关键：环的存在被翻译成「两个不同速度的指针会不会相遇」，
    而这个判断只需要两个指针变量。链表结构见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数最多 10^4，值域 -10^5..10^5。设环外长度 a、环长 c，
    slow 进环最多 a 步、进环后最多 c 步追平，总步数 O(a + c) = O(n)；
    fast 走两倍，仍是 O(n)。额外空间 O(1)，正好满足进阶要求。

    另一条思路是把访问过的节点丢进 set，再次访问到就说明有环：时间同样 O(n)，
    但要存下最多 10^4 个节点的引用，空间 O(n)，进阶要求的常数空间做不到。
    注意用 set 时存的必须是节点对象（按身份哈希），存 val 会把值重复的链判成有环。

坑在哪：
  1. 相遇判断必须用 `is` 比身份，不能用 `==` 比 val。链表值可以重复，
     样例一的 [3,2,0,-4] 若换成全 3 的链，按 val 比第一轮就误报有环；
  2. 循环条件要同时检查 `fast` 和 `fast.next`。少判 `fast.next`，
     在偶数长度的无环链上 `fast.next.next` 会 AttributeError；
  3. 判相遇要放在两个指针都移动**之后**。放在移动前的话，起手 slow 与 fast
     同为 head，一进循环就判定相等，任何链都会被判成有环；
  4. 空链与单节点自动落到返回 False：while 的条件一开始就不成立。

样例复核：
    [3,2,0,-4]，尾节点 -4 接回下标 1 的节点 2，环长 3、环外长度 1。
    起手两者都在 3。第一轮 slow 到 2、fast 到 0；第二轮 slow 到 0、
    fast 走 -4 再绕回 2；第三轮 slow 到 -4、fast 从 2 走两步也到 -4，
    身份相同，返回 True，与样例一致。
"""
from typing import List, Optional


class Solution:
    def hasCycle(self, head: "Optional[ListNode]") -> bool:
        # 两个指针同一起点，速度差 1；有环时间距每轮减 1，必然归零
        slow = head
        fast = head
        # fast 一次跨两格，所以 fast 和 fast.next 都得存在才敢走
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            # 比身份而不是比 val：链上允许出现重复值
            if slow is fast:
                return True
        # fast 摸到了链尾的 None，说明这条链是有限长的直线
        return False
