"""LC23 合并 K 个升序链表 —— 把 k 条各自升序的链表合成一条升序链表并返回。

这题考什么：
    每条链自己有序，所以全局最小值一定是某条链的**当前表头**，
    候选只有 k 个。问题变成「反复从 k 个候选里取最小、取走后补上它的后继」，
    这正是最小堆（优先队列，见 docs/ds/heap.md）的用途。

    做法：先把 k 个非空表头入堆；每次弹出堆顶接到结果链尾部，
    若它还有后继就把后继入堆。堆里任何时刻最多 k 个元素（每条链只贡献一个），
    弹 N 次、每次调整 O(log k)，总共 O(N log k)。

    不用堆的等价做法是两两归并：把 k 条链折半配对合并，做 log k 轮，
    每轮扫过全部 N 个节点，同样 O(N log k)，而且额外空间是 O(1)。
    最朴素的「拿结果链去和第 i 条链合并」则是 O(N * k)，见下面的量级估算。

数据规模与复杂度：
    k 最多 10^4，所有链的节点总数 N 不超过 10^4，值域 -10^4..10^4。
    堆解法 O(N log k)，约 10^4 * 14 = 1.4 * 10^5 次比较，随手过。
    逐条依次合并是 O(N * k)：k 条链每条都要把已合并的前缀重新扫一遍，
    最坏 10^4 * 10^4 = 10^8 次指针比较，Python 下必然超时。

坑在哪：
  1. 入堆的元组不能只写 (node.val, node)。val 相等时 Python 会继续比较下一项，
     也就是拿两个 ListNode 相互 `<`，而 ListNode 没有定义比较运算，
     直接 TypeError。样例一的三条链里有两个 1，第一次弹堆就会踩到。
     插一个整数下标 i 当**破平键**：val 相等时改比 i，永远比不到节点身上；
  2. 下标 i 取「链的编号」而不是入堆序号也够用——同一条链任何时刻只有一个节点在堆里，
     所以 (val, i) 这个二元组在堆内一定唯一，绝不会退到第三项；
  3. 空链不能入堆。题面允许 lists[i] 为空链（样例三的 [[]]），
     也允许整个 lists 为空（样例二），入堆前必须判一次非空，否则取 .val 就 AttributeError；
  4. 结果链的尾巴不用手动置 None。最后弹出的节点是全局最大值，
     它若还有后继，后继早就入了堆、循环还会继续，所以循环结束时它的 next 本来就是 None；
  5. 返回 dummy.next。dummy 是值为 0 的占位节点，直接返回它会在结果最前面多个 0。

样例复核：
    [[1,4,5],[1,3,4],[2,6]]。初始堆 (1,0)、(1,1)、(2,2)。
    弹 (1,0) 接 1、推入 (4,0)；弹 (1,1) 接 1、推入 (3,1)；
    弹 (2,2) 接 2、推入 (6,2)；弹 (3,1) 接 3、推入 (4,1)；
    此后两个 4 靠下标 0 < 1 决出先后，再弹 5、6。
    结果 [1,1,2,3,4,4,5,6]，与样例一致。
"""
import heapq
from typing import List, Optional


class Solution:
    def mergeKLists(self, lists: "List[Optional[ListNode]]") -> "Optional[ListNode]":
        heap = []
        # 先放入每条链的表头：全局最小值必在这 k 个候选之中
        for i, node in enumerate(lists):
            # 题面允许某条链是空的，空链没有可比的 val，不能入堆
            if node:
                # 第二项 i 是破平键：val 相等时改比整数下标，绝不会比到 ListNode 上
                heapq.heappush(heap, (node.val, i, node))
        # 哨兵让「接第一个节点」和后续写法一致
        dummy = ListNode(0)
        cur = dummy
        while heap:
            _, i, node = heapq.heappop(heap)   # 堆顶就是当前所有候选里最小的
            cur.next = node                    # 直接复用原节点，不新建
            cur = node
            # 补上这条链的下一个候选，沿用同一个 i：一条链同时只有一个节点在堆里
            if node.next:
                heapq.heappush(heap, (node.next.val, i, node.next))
        # 最后弹出的是全局最大值，它没有后继（有的话堆还不空），next 天然是 None
        return dummy.next
