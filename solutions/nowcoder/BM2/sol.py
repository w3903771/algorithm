# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/b58434e200a648c589ca2063f1faf58c
# 判题: 核心代码模式
# 签名: reverseBetween(head: ListNode、m: integer、n: integer) -> ListNode

"""BM2 链表内指定区间反转 —— 哑节点定位第 m 个的前驱，再用头插法把区间逐个提到最前。

这题考什么：
    区间反转比整表反转多两件麻烦事：**接口要缝回去**，而且 m 可能就是 1，
    此时区间头没有前驱。后者用**哑节点**（dummy head，值无意义、只为让每个真实
    节点都有前驱的辅助节点）统一掉：dummy.next = head，最后返回 dummy.next，
    头换没换都不用管。

    定位：从 dummy 往后走 m-1 步，pre 停在区间前一个节点，cur = pre.next 是区间第一个节点。

    反转用**头插法**，做 n-m 次，每次把 cur 后面那个节点摘下来插到 pre 之后：

        nxt = cur.next          待搬运的节点
        cur.next = nxt.next     把它从原位摘掉
        nxt.next = pre.next     插到区间最前面
        pre.next = nxt

    循环不变量是「cur 始终是区间里位置最靠后的节点」：它一开始是区间头，
    每搬走一个后继就相对后退一位，结束时正好是区间尾，它的 next 从头到尾
    一直指着区间外的第一个节点，右接口自动缝好；左接口由 pre.next 维护。
    这比「先把区间切下来反转再接回去」少记两个端点，也不会中途断链。
    链表基本操作见 docs/ds/linked-list.md。

数据规模与复杂度：
    链表长度 size <= 1000，0 < m <= n <= size，|val| <= 1000，其他语言时限 2 秒。
    定位 m-1 步、头插 n-m 次，两段加起来不超过 size 次指针改写，
    时间 O(size)、额外空间 O(1)，达到题面进阶要求。
    朴素做法是把区间的值取出来放进列表再倒着写回，时间同阶但要 O(n-m) 空间，
    而且题意是重排节点，改值的写法在「节点带其他字段」的场景下就不成立了。

坑在哪：
  1. 没有哑节点时 m == 1 是个必须单写的分支：区间头就是表头，pre 无处可放。
     加了哑节点，`for _ in range(m - 1)` 一步都不走，pre 停在 dummy，代码一条路走到底；
  2. 结尾必须 `return dummy.next` 而不是 `return head`。m == 1 时 head 已经被
     头插法挤成了区间尾，返回 head 会丢掉它前面反转好的所有节点；
  3. 头插次数是 n-m 而不是 n-m+1。多做一次会把区间右边第一个节点也拖进来，
     反转范围整体越界；m == n 时次数为 0，链表原样返回，对应样例二的 {5},1,1；
  4. cur 全程不前移。写成「每轮 cur = cur.next」是把头插法和 BM1 的三指针法
     混在一起，cur 越过区间尾之后再摘节点就会把区间外的链接改坏。

样例复核：
    {1,2,3,4,5}，m = 2、n = 4。pre = 1，cur = 2，头插 2 次。
    第一次搬 3：链变成 1,3,2,4,5，cur 仍是 2；第二次搬 4：链变成 1,4,3,2,5。
    cur = 2 的 next 一直是 5，右接口没断，输出 {1,4,3,2,5}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def reverseBetween(self, head: "Optional[ListNode]", m: int, n: int) -> "Optional[ListNode]":
        dummy = ListNode(0)         # 哑节点：m == 1 时也有前驱可用，省掉换头分支
        dummy.next = head
        pre = dummy
        # 从 dummy 走 m-1 步：dummy 相当于第 0 个节点，走完 pre 就是第 m 个的前驱
        for _ in range(m - 1):
            pre = pre.next
        cur = pre.next              # 区间第一个节点，反转后会变成区间尾，位置不动
        # 头插 n-m 次：每次把 cur 的后继摘下来插到 pre 之后，区间就一位位翻过来
        for _ in range(n - m):
            nxt = cur.next
            cur.next = nxt.next     # 摘掉 nxt，cur 的 next 始终指向区间外，右接口不断
            nxt.next = pre.next     # 插到区间最前
            pre.next = nxt
        return dummy.next           # 头可能已被换掉，只能从哑节点取新表头
