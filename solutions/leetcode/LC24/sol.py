"""LC24 两两交换链表中的节点 —— 相邻两个节点为一组互换位置，只改指针不改 val。

这题考什么：
    交换两个相邻节点 a、b（顺序 prev -> a -> b -> rest），需要重接**三条边**，
    而且顺序不能乱：

        a.next = b.next     a 跳过 b 直接连到 rest，先做是因为 b.next 马上要被覆盖
        b.next = a          b 反过来指向 a，这一对内部完成对调
        prev.next = b       让前驱认新的组头 b

    做完之后 a 变成了这一对的尾巴，正好是下一对的前驱，令 prev = a 继续。
    整个过程的循环不变量是「prev 指向已处理完部分的最后一个节点」。

    题目明说不能只交换 val，所以必须真的动指针。链表指针搬移的基本套路见
    docs/ds/linked-list.md。

    哨兵节点在这里是必需的：第一对交换后表头会从 head 变成 head.next，
    没有哨兵就得为「第一对」单写一段代码。

数据规模与复杂度：
    节点数最多 100。一趟遍历 O(n) 时间，每对只做常数次指针赋值；
    额外空间 O(1)，只有哨兵与三个临时指针。
    递归写法（交换前两个再递归处理剩余）也是 O(n) 时间，但栈深 n / 2 层，
    本题 50 层无碍，换成节点数上万的题就会触到 Python 默认 1000 层递归上限。

坑在哪：
  1. 三条边的改动顺序不能颠倒。先写 `b.next = a` 的话，b 原来的后继 rest
     就丢了，链表当场断在这一对后面；
  2. 循环条件必须同时检查 `prev.next` 和 `prev.next.next`。只检查前者，
     链表剩下奇数个节点时 b 会是 None，`b.next` 直接 AttributeError；
     剩单个节点时题面要求原样保留，正是靠这个条件自然跳过；
  3. 交换后 prev 要移到 a 而不是 b。b 是新的组头、a 才是新的组尾，
     移到 b 会让下一轮把 a 和它后面的节点当成一对，交换结果错位；
  4. 空链与单节点不必特判：while 一次都不进，返回 dummy.next 就是原样，
     对应样例二和样例三。

样例复核：
    [1,2,3,4]。第一轮 prev = dummy、a = 1、b = 2：1.next = 3，2.next = 1，
    dummy.next = 2，prev 移到 1，链变成 2 -> 1 -> 3 -> 4。
    第二轮 a = 3、b = 4：3.next = None，4.next = 3，1.next = 4，
    链变成 2 -> 1 -> 4 -> 3。prev 移到 3，prev.next 为 None 退出，与样例一致。
"""
from typing import List, Optional


class Solution:
    def swapPairs(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # 哨兵补出「第一对的前驱」，第一对交换后表头会变，没有它就得单独处理
        dummy = ListNode(0)
        dummy.next = head
        prev = dummy
        # 两个条件缺一不可：剩不足两个节点时就该停手，剩单个节点按题面原样保留
        while prev.next and prev.next.next:
            a = prev.next
            b = a.next
            # 三条边按此顺序改：先让 a 记住 b 的后继，否则下一句就把它覆盖掉了
            a.next = b.next
            b.next = a
            prev.next = b
            # 交换后 a 成了这一对的尾节点，正是下一对的前驱
            prev = a
        return dummy.next                # 表头已经换成原来的第二个节点
