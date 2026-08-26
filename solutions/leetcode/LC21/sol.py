"""LC21 合并两个有序链表 —— 把两条各自升序的链表拼成一条升序链表，节点直接复用不新建。

这题考什么：
    归并排序的 merge 步骤本身（见 docs/basic/sorting.md）。
    两条链都已经有序，那么全局最小值只可能是两个表头之一——
    比较这两个头、取小的接到结果尾部、让它所在的链前进一格，重复到有一条走空。

    循环不变量是「已接出的结果段有序，且它的每个值都不大于两条剩余链的任何值」。
    因为剩余链自身有序，只要每轮都在两个头里取更小的那个，不变量就一直成立。

    一条链走空后，另一条剩下的整段已经有序、且全都不小于结果段，
    直接把整段接上即可，不必逐个节点搬——这一步能省掉一半的循环次数。

    结果链用的是原来的节点对象，没有新建任何节点，也没有改动任何 val，
    改的只有 next 指针。链表指针操作见 docs/ds/linked-list.md。

数据规模与复杂度：
    两条链各最多 50 个节点，值域 -100..100。时间 O(m + n)，
    每个节点只被访问一次；额外空间 O(1)，只有哨兵和一个游标。
    递归写法（比较两个头之后递归合并剩余部分）同样 O(m + n) 时间，
    但递归深度等于 m + n，本题 100 层没问题，节点数上万的同类题就会爆栈。

坑在哪：
  1. 比较要用 `<=` 而不是 `<`。两边值相等时取 list1 才能保证**稳定**——
     相等元素维持原来的先后关系。用 `<` 虽然结果序列的数值一样，
     但在按 key 排序、节点还带别的字段的场景里会悄悄打乱顺序；
  2. 收尾那句 `cur.next = list1 if list1 else list2` 不能漏。漏了的话结果链
     会停在两条链首次分出胜负的位置，长的那条链的尾巴全部丢失；
  3. 空链不必特判。list1 为空时 while 一次都不进，收尾直接把 list2 整条接上，
     对应样例三；两条都空则接上 None，返回空链，对应样例二；
  4. 返回 dummy.next 而不是 dummy。dummy 是值为 0 的占位节点，
     返回它会在结果最前面多出一个凭空的 0。

样例复核：
    [1,2,4] 与 [1,3,4]。取 list1 的 1（相等取左），取 list2 的 1，
    取 2（2 < 3），取 3（3 < 4），取 list1 的 4（相等取左），list1 走空，
    把 list2 剩下的 [4] 整段接上。结果 [1,1,2,3,4,4]，与样例一致。
"""
from typing import List, Optional


class Solution:
    def mergeTwoLists(self, list1: "Optional[ListNode]", list2: "Optional[ListNode]") -> "Optional[ListNode]":
        # 哨兵省掉「结果链还空着」的分支，cur 始终是结果链的最后一个节点
        dummy = ListNode(0)
        cur = dummy
        # 只要两条都还有节点，就必须逐个比较；有一条空了循环立刻结束
        while list1 and list2:
            # 相等时取 list1，保证稳定：原本靠前的相等元素仍然靠前
            if list1.val <= list2.val:
                cur.next = list1
                list1 = list1.next
            else:
                cur.next = list2
                list2 = list2.next
            cur = cur.next
        # 剩下那条整段有序且全都不小于已接出的部分，一次接上即可
        cur.next = list1 if list1 else list2
        return dummy.next                # 跳过哨兵占位节点
