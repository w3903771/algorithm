# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/d8b6b4358f774294a89de2a6ac4d9337
# 判题: 核心代码模式
# 签名: Merge(pHead1: ListNode、pHead2: ListNode) -> ListNode

"""BM4 合并两个排序的链表 —— 哑节点 + 双指针，每次接走两个当前头里较小的那个。

这题考什么：
    归并排序的 merge 步骤搬到链表上（归并排序见 docs/basic/sorting.md）。
    两条链各自有序，所以结果链的下一个节点一定是两个当前头里较小的那个：
    接走它、该链指针后移，直到有一条走空。

    链表比数组省事的地方在收尾：**剩下那条不用逐个搬**，
    直接把整段挂到结果链尾巴上就行，这是「只有 next 指针、没有物理相邻性」的红利。

    哑节点（dummy head，值无意义的辅助表头）省掉「结果链现在还是空的」这个分支——
    否则每次接入都要先判一次「这是不是第一个节点」。tail 始终指向已建好部分的最后一个节点，
    这就是整个循环的不变量。

数据规模与复杂度：
    单链长度 n <= 1000，节点值在 [-1000, 1000]，其他语言时限 2 秒。
    每个节点恰好被接走一次，时间 O(n + m)、额外空间 O(1)（只重接指针，不新建节点）。
    先把两条链的值倒进列表、排序、再建链也是 O((n+m) log(n+m))，
    既慢一个 log 又多花 O(n+m) 空间，还浪费了「两条链本来就有序」这个前提。

坑在哪：
  1. 循环结束后必须补一句 `tail.next = a if a else b`。while 的退出条件是
     两条链有一条走空，另一条剩下的节点还挂在原处，漏掉这句就直接丢掉一整段后缀；
  2. 取 `<=` 而不是 `<`。相等时优先取第一条，合并是稳定的。本题只比数值，
     稳不稳定看不出来，但在「按 key 排序、相同 key 要保持原有先后」的场景里这一笔是致命的；
  3. 两条链都可能为空（样例二就是 {},{}）。有哑节点时 dummy.next 从头到尾没被写过，
     返回的就是 None，正好是空链表，不需要任何特判；
  4. 返回 dummy.next 而不是 dummy。dummy 是本地造的辅助节点，它的 val 是 0，
     交上去会在结果最前面多出一个凭空的 0。

样例复核：
    {1,3,5} 与 {2,4,6}。依次比较 1<=2 取 1、3>2 取 2、3<=4 取 3、5>4 取 4、5<=6 取 5，
    此时 a 走空，把 b 剩下的 6 整段挂上，得到 {1,2,3,4,5,6}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def Merge(self, pHead1: "Optional[ListNode]", pHead2: "Optional[ListNode]") -> "Optional[ListNode]":
        dummy = ListNode(0)         # 哑节点：省掉「结果链为空」的分支，也兜住两条链全空
        tail = dummy                # 不变量：tail 永远是已建好部分的最后一个节点
        a, b = pHead1, pHead2
        # 两条都还有节点时才需要比较；任一条走空就跳出去做整段挂接
        while a and b:
            if a.val <= b.val:      # <= 保证相等时取第一条，合并稳定
                tail.next = a
                a = a.next
            else:
                tail.next = b
                b = b.next
            tail = tail.next
        # 有一条走空了；另一条剩下的部分本身有序，整段挂上即可，不必逐个搬
        tail.next = a if a else b   # 两条都空时挂的是 None，结果就是空链表
        return dummy.next
