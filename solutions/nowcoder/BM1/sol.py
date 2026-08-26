# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/75e878df47f24fdc9dc3e400ec6058ca
# 判题: 核心代码模式
# 签名: ReverseList(head: ListNode) -> ListNode

"""BM1 反转链表 —— 把单链表每条边的指向掉个头，返回原来的尾节点作为新表头。

这题考什么：
    链表反转的本质是**改边的方向**，不是搬运节点值。把链表看成一串单向的边，
    反转就是逐条边取反，节点对象一个都不用新建，val 一个都不用动。
    链表的结构与指针搬移见 docs/ds/linked-list.md。

    维护两个指针：prev 指向「已经反转好的那一段的头」，cur 指向「还没处理的那一段的头」。
    每一轮做四件事，顺序不能乱：

        nxt = cur.next      先把后路存下来，否则改完 cur.next 就找不到剩下的链
        cur.next = prev     掉头
        prev = cur          已完成段前移
        cur = nxt           待处理段前移

    循环不变量是「prev 是反转好的那段的头，cur 是原顺序剩余段的头，两段无交集」。
    cur 变成 None 时剩余段为空，prev 正好停在原链表的最后一个节点，也就是新表头。

数据规模与复杂度：
    n <= 1000，其他语言时限 2 秒。一趟遍历 O(n) 时间、O(1) 额外空间，
    最坏也就一千次指针赋值，量级上没有任何压力。
    另一条思路是把 val 收进列表再倒序建新链，时间同样 O(n)，
    但要多开 O(n) 空间、多造 n 个节点对象，不满足题面「空间复杂度 O(1)」。

坑在哪：
  1. `nxt = cur.next` 必须写在 `cur.next = prev` **之前**。顺序反过来，
     cur.next 已经被覆盖成 prev，nxt 拿到的是前一个节点，链表当场退化成
     两个节点来回打转，循环再也走不到 None；
  2. 返回值是 prev 不是 cur。循环退出时 cur 已经是 None，返回 cur 等于交了个空链表；
  3. 空链表与单节点不必特判：head 为 None 时 while 一次都不进，返回 prev = None，
     对应样例二的空表；单节点进一次循环，它的 next 被置成 None 后原样返回。

样例复核：
    输入 {1,2,3}。第一轮：1.next = None，prev = 1，cur = 2；
    第二轮：2.next = 1，prev = 2，cur = 3；第三轮：3.next = 2，prev = 3，cur = None。
    返回 prev = 3，整条链是 {3,2,1}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def ReverseList(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # prev 起手取 None：它既是「已反转段的头」，也兼作新链尾节点的终止标记
        prev = None
        cur = head
        # 每轮掉头一条边；cur 走到 None 说明原链的边已经全部处理完
        while cur:
            nxt = cur.next      # 先存后路：下一句就要把 cur.next 覆盖掉
            cur.next = prev     # 掉头，这条边由「指向后继」变成「指向前驱」
            prev, cur = cur, nxt
        return prev             # cur 走到 None 时 prev 停在原尾节点，即新表头
