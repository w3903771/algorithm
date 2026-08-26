# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/b49c3dc907814e9bbfa8437c251b028e
# 判题: 核心代码模式
# 签名: reverseKGroup(head: ListNode、k: integer) -> ListNode

"""BM3 链表中的节点每k个一组翻转 —— 每组开工前先探路数够 k 个再翻，不够就原样收尾。

这题考什么：
    在 BM2 区间反转的基础上多了一条规矩：**不足 k 个的尾巴保持原样**。
    于是每组动手之前必须先「探路」——从 pre 往后数 k 步，数不满就直接结束，
    绝不能翻到一半发现不够再回滚：链表已经改了指针，回滚要再写一遍反向逻辑，
    比先探路复杂得多。

    循环体（pre 是当前组的前驱，哑节点保证第一组也有前驱）：
      1. 探路：从 pre 往后走 k 步，中途碰到 None 就把剩下的尾巴原样留着并返回；
      2. 翻转：仍用 BM2 的头插法翻 k-1 次，cur = pre.next 是组头，翻完自动变成组尾；
      3. 前移：pre = cur，也就是本组翻完后的最后一个节点，做下一组的前驱。

    题面明确「不能更改节点中的值，只能更改节点本身」，所以只能重接指针，
    不能用「按组把值倒过来写」这种偷懒写法。链表操作见 docs/ds/linked-list.md。

数据规模与复杂度：
    0 <= n <= 2000，1 <= k <= 2000，0 <= val <= 1000，其他语言时限 2 秒。
    每个节点被探路访问一次、被头插搬运一次，合计 2n 次指针操作，
    时间 O(n)、额外空间 O(1)，满足题面要求。
    n 和 k 都只有 2000，即使写成「每组重新从头遍历定位」的 O(n * n / k) 也能过，
    但探路 + 头插的写法一趟到底，没有理由退而求其次。

坑在哪：
  1. 探路必须在翻转之前完成。先翻后查会留下一组翻了一半的链表，
     而题面要求不足 k 的尾巴**原封不动**，样例 k = 3 的 {1,2,3,4,5} 输出
     {3,2,1,4,5} 就是这条规矩的直接体现；
  2. 探路循环里每走一步就判空并立刻 `return dummy.next`。等 k 步走完再判空，
     probe 早就在 None 上取 next 抛 AttributeError 了；
  3. k > n 时第一次探路就失败，整条链原样返回；k == 1 时头插 0 次，
     等价于原链表，代码开头直接把这两种情况短路掉，省掉空转；
  4. pre 前移到的是 cur 而不是 pre.next。翻完这一组后 pre.next 是组头（新的第一个），
     cur 才是组尾，用错了会让下一组的前驱指到组中间，链表结构错乱。

样例复核：
    {1,2,3,4,5}，k = 2。第一组探路到 2，头插 1 次得 2,1,3,4,5，pre 移到 1；
    第二组探路到 4，头插 1 次得 2,1,4,3,5，pre 移到 3；
    第三组从 5 往后只有一个节点，探路失败，5 原样留下。输出 {2,1,4,3,5}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def reverseKGroup(self, head: "Optional[ListNode]", k: int) -> "Optional[ListNode]":
        # k == 1 翻了等于没翻，空链表也无事可做，先短路掉省去整轮空转
        if k <= 1 or head is None:
            return head
        dummy = ListNode(0)         # 哑节点：第一组也需要前驱，且表头必被换掉
        dummy.next = head
        pre = dummy
        while True:
            # 探路：先确认后面还有整整 k 个节点。每走一步就判空，
            # 数不满就把尾巴原样留着直接交卷，绝不翻到一半再回滚
            probe = pre
            for _ in range(k):
                probe = probe.next
                if probe is None:
                    return dummy.next
            # 头插法翻转本组：cur 是组头，被后继一个个挤到后面，翻完正好是组尾
            cur = pre.next
            for _ in range(k - 1):
                nxt = cur.next
                cur.next = nxt.next
                nxt.next = pre.next
                pre.next = nxt
            pre = cur               # 组尾成为下一组的前驱，不能写成 pre.next
