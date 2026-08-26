"""LC25 K 个一组翻转链表 —— 每 k 个节点为一组就地翻转，不足 k 个的尾巴保持原样。

这题考什么：
    在 LC206 的整链翻转之上加两件事：**先确认这一组凑得满**，以及**把翻转好的组重新缝回**。

    每一组的处理分三步：
      1. 探路。从 group_prev（本组前驱）往后数 k 步，中途撞到 None 就说明剩余不足一组，
         按题面要求原样保留，直接返回结果。数满则 kth 落在本组最后一个节点上；
      2. 翻转。把 [group_prev.next, kth] 这一段按 LC206 的四步法翻转。
         关键技巧是 prev 起手不取 None 而取 group_next（下一组的头）——
         这样翻转结束时本组尾节点已经连好下一组，省掉事后再补一次接线；
      3. 缝合。翻转后本组的新头是 kth、新尾是原来的组头 tail。
         令 group_prev.next = kth，再把 group_prev 移到 tail，进入下一组。

    循环不变量：group_prev 始终指向「已经处理完的部分」的最后一个节点，
    它的 next 之后才是待处理的链。链表指针搬移见 docs/ds/linked-list.md。

数据规模与复杂度：
    1 <= k <= n <= 5000，val 取 0..1000。探路走 k 步、翻转走 k 步，
    每组常数倍工作量，总时间 O(n)（每个节点被摸到的次数不超过 2）。
    额外空间只有几个指针，O(1)，满足进阶要求。

    递归写法（翻转头 k 个之后递归处理剩下的）时间也是 O(n)，但递归深度是 n / k，
    k = 1 时深度就是 n = 5000，**超过 Python 默认的 1000 层递归上限**，
    直接 RecursionError。迭代版没有这个隐患。

坑在哪：
  1. 探路必须在翻转**之前**完成。先翻转再发现凑不满一组，链已经被改坏，
     还得原路翻回去，代码立刻翻倍；
  2. 探路从 group_prev 出发数 k 步，而不是从组头数 k 步。从组头数 k 步会落到
     下一组的第一个节点上，缝合时全部错位一格；
  3. 内层翻转的终止条件是 `cur is not group_next`，不是 `cur`。
     写成 `while cur` 会一路翻到链尾，把后面所有组也翻掉；
  4. 内层 prev 起手取 group_next 而不是 None。取 None 的话本组尾节点的 next
     会被置空，整条链在这里断掉，得额外再接一次；
  5. group_prev 要移到 tail（翻转后的组尾）而不是 kth（翻转后的组头）。
     移到 kth 会让下一组的前驱指错位置，缝出来的链顺序全乱；
  6. k = 1 时算法仍然正确：每组只有一个节点，翻转是空操作，走 n 轮后原样返回。

样例复核：
    [1,2,3,4,5]、k = 3。第一组探路数 3 步落在节点 3，group_next = 4。
    翻转 1 -> 2 -> 3 得到 3 -> 2 -> 1 -> 4，dummy.next 改成 3，group_prev 移到节点 1。
    第二组从节点 1 往后数 3 步：4、5、然后是 None，凑不满，直接返回。
    结果 [3,2,1,4,5]，与样例二一致。
"""
from typing import List, Optional


class Solution:
    def reverseKGroup(self, head: "Optional[ListNode]", k: int) -> "Optional[ListNode]":
        # 哨兵补出第一组的前驱：第一组翻转后表头会变成原来的第 k 个节点
        dummy = ListNode(0)
        dummy.next = head
        group_prev = dummy
        while True:
            # 探路：从本组前驱往后数 k 步，落点 kth 就是本组的最后一个节点
            kth = group_prev
            for _ in range(k):
                kth = kth.next
                # 中途撞到 None 说明剩余不足 k 个，题面要求原样保留，就此收工
                if kth is None:
                    return dummy.next
            group_next = kth.next            # 下一组的头，翻转时当作本组的终止标记
            # 翻转 [group_prev.next, kth]：prev 起手取 group_next，
            # 于是本组尾节点翻转后自动连上下一组，不必事后补接
            prev = group_next
            cur = group_prev.next
            while cur is not group_next:     # 走到下一组的头就停，不要越界翻到后面
                nxt = cur.next               # 先存后路，下一句会覆盖 cur.next
                cur.next = prev
                prev = cur
                cur = nxt
            # 翻转后新头是 kth、新尾是原来的组头
            tail = group_prev.next
            group_prev.next = kth            # 把上一段缝到本组新头上
            group_prev = tail                # 新尾成为下一组的前驱
