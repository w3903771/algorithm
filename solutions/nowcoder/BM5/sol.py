# 来源: 牛客 · 面试必刷TOP101　较难
# 链接: https://www.nowcoder.com/practice/65cfde9e5b9b4cf2b6bafa5f3ef33fa6
# 判题: 核心代码模式
# 签名: mergeKLists(lists: list<ListNode>) -> ListNode

"""BM5 合并k个已排序的链表 —— 小根堆里始终只放 k 个「当前头」，每次弹最小的接走。

这题考什么：
    把 BM4 的两路归并推广到 k 路。逐条往结果里并要 O(nk)：第 i 次合并时
    结果链已有的节点会被重新扫一遍。观察 BM4 的循环，每一步其实只做一件事——
    「在所有链的当前头里挑最小」——k 路就用**小根堆**（每次能 O(log k) 取出最小元素
    的完全二叉树结构，Python 标准库 heapq，见 docs/ds/heap.md）
    来做这个挑选。堆里永远只有 k 个元素，每条链贡献一个头，弹出一个就补上它的后继。

    入堆元素做成三元组 `(val, 序号, 节点)`：heapq 比较元组时前一项相等就接着比后一项，
    而 **ListNode 没有实现 __lt__**，val 撞车就会直接 TypeError。中间这个全局递增的
    序号是**破平键**，保证比较最迟在第二项分出胜负，永远轮不到节点参与比较。

    另一条路是分治两两合并，复杂度同为 O(n log k)，但要多写一层递归/分层循环，
    而堆的写法一趟到底、常数更小。

数据规模与复杂度：
    节点总数 n <= 5000，|val| <= 1000，k 由输入的链表条数决定，其他语言时限 2 秒。
    每个节点入堆一次、出堆一次，各 O(log k)，总计 O(n log k)；
    堆里最多 k 个三元组，额外空间 O(k)，结果链复用原节点不新建。
    朴素的逐条归并在 k 条等长链时是 5000 * k 级别的重复扫描，
    本题 n 只有 5000 还能过，但堆的写法不受 k 增长影响，是可以带走的通法。

坑在哪：
  1. 三元组里的破平键不能省。少了它，两条链的当前头 val 相同时 heapq 会去比较
     两个 ListNode，抛 TypeError: '<' not supported between instances of 'ListNode'；
  2. 破平键的起始值取 len(lists) 而不是 len(heap)。入参里夹着的空链表在建堆时
     被过滤掉了，heap 比 lists 短，用 len(heap) 当起点会和已经在堆里的下标撞车，
     撞车的那一刻破平键失效，又退回去比较 ListNode；
  3. 入参可能是空列表，也可能整条是 None（题面允许链表为空）。建堆时统一用
     `if node` 过滤，堆为空则 while 一次不进，返回 dummy.next = None，就是空表；
  4. 结尾的 `tail.next = None` 在正常输入下是空操作——循环退出说明最后弹出的节点
     没有后继——但它把「结果链尾一定终止」这件事写死在代码里，
     是零成本的防御，读者不必再去反推最后一个节点的 next 是什么。

样例复核：
    [{1,2},{1,4,5},{6}]。堆初始为 (1,0,·)、(1,1,·)、(6,2,·)，两个 1 靠破平键分先后，
    先弹链 0 的 1，补进 (2,3,·)；再弹链 1 的 1，补进 (4,4,·)；
    之后依次弹 2、4、5、6，得到 {1,1,2,4,5,6}，与样例一致。
"""
import heapq
from typing import List, Optional


class Solution:
    def mergeKLists(self, lists: "List[Optional[ListNode]]") -> "Optional[ListNode]":
        lists = lists or []                 # 入参允许为空，统一成列表再往下走
        # (val, 序号, 节点)：序号是破平键，避免 val 相等时 heapq 去比较不可比较的 ListNode
        heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
        heapq.heapify(heap)                 # 原地建堆 O(k)，比逐个 heappush 快一档
        # 起始序号取 len(lists) 而不是 len(heap)：入参里可能夹着空链表被过滤掉，
        # 用 len(heap) 会和已在堆里的下标撞车，破平键失效又会退回去比较 ListNode
        seq = len(lists)
        dummy = ListNode(0)                 # 哑节点：省掉「结果链为空」的分支
        tail = dummy
        # 堆顶恒为所有链当前头里的最小值，弹一个接一个，弹空即全部并完
        while heap:
            _, _, node = heapq.heappop(heap)
            tail.next = node
            tail = node
            if node.next:                   # 弹走谁就补上谁的后继，堆里始终不超过 k 个
                heapq.heappush(heap, (node.next.val, seq, node.next))
                seq += 1
        tail.next = None                    # 收口：把「结果链到此为止」写死，不靠推理
        return dummy.next
