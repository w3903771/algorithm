"""LC138 随机链表的复制 —— 链表节点除 next 外还有一个可以指向任意节点（或 null）的 random 指针，要求做一份深拷贝。

这题考什么：
    难点只有一个：复制 random 时，它指向的那个**副本可能还没被创建**。
    单趟从头到尾复制，遇到 `cur.random` 指向后面的节点就无从下手。
    所以核心是建立「原节点 -> 它的副本」这张对应表。

    最省事的写法是用字典存这张表（第一趟只造节点、第二趟按表接 next 与 random），
    空间 O(n)。本文件用的是**交织法**，把对应表编码进链表结构本身，额外空间 O(1)：

      1. 把每个副本插在它的原节点正后面，链变成 A -> A' -> B -> B' -> C -> C'。
         此时「X 的副本」就是 `X.next`，对应表不用另外存；
      2. 遍历原节点 X，若 `X.random` 指向 Y，则 Y 的副本是 `Y.next`，
         于是 `X.next.random = X.random.next`。一句话搞定所有 random；
      3. 把交织的链拆回两条：原链复原、副本链独立返回。

    第二步之所以成立，全靠第一步保证的不变量「每个原节点的正后方就是它的副本」，
    这个不变量在第三步之前必须一直维持，所以三趟不能合并成两趟。
    链表结构见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数 n 最多 1000，val 取 -10^4..10^4。三趟遍历都是 O(n)，
    合计 O(n) 时间；除输出的 n 个副本节点外只用几个游标，额外空间 O(1)。
    字典法同样 O(n) 时间，但要多一张 n 项的哈希表；n 只有 1000 时两者都够快，
    交织法的价值在于说明「对应关系可以编码进结构本身」这个思路。

    真正过不了的是暴力法：对每个副本去原链里线性查找 random 的下标再定位，
    O(n^2) = 10^6 次指针跳转，本题规模还能过，但换成 10^5 个节点就是 10^10，
    这也是题面把 random 设计成任意指向的原因。

坑在哪：
  1. random 可以是 null，接线前必须判一次。不判的话 `X.random.next` 在
     X.random 为 None 时直接 AttributeError，样例一第一个节点的 random 就是 null；
  2. random 可以指向**自己**，也可以有多个节点指向同一个目标。交织法对这两种
     情况天然正确，因为它查的是「目标节点的正后方」，与谁指过来无关；
  3. 第三步拆链时必须把原链也复原。留着交织状态返回，等于把调用方传进来的
     输入改坏了——题面要求的是拷贝，不是搬走；
  4. 拆链时副本的 next 要判空。最后一个副本后面已经没有节点，
     写成 `copy.next = copy.next.next` 会在末尾 AttributeError；
  5. 空链要先挡掉。head 为 None 时后面每一趟都用不到，直接返回 None 最干净。

样例复核：
    [[7,null],[13,0],[11,4],[10,2],[1,0]]，即 7 的 random 为空、13 指向下标 0、
    11 指向下标 4、10 指向下标 2、1 指向下标 0。
    交织后链为 7,7',13,13',11,11',10,10',1,1'。
    接 random：13 的 random 是节点 7，7 的副本是 7.next 即 7'，于是 13'.random = 7'；
    11 的 random 是节点 1，得 11'.random = 1'；10 指向 11，得 10'.random = 11'；
    1 指向 7，得 1'.random = 7'。拆链后副本的 random 下标依次是
    null、0、4、2、0，与期望输出一致。
"""
from typing import List, Optional


class Solution:
    def copyRandomList(self, head: "Optional[Node]") -> "Optional[Node]":
        # 空链没有可交织的节点，后面三趟全是空转，先挡掉
        if head is None:
            return None
        # 第一趟：把副本插在原节点正后方，链变成 A -> A' -> B -> B' -> ...
        # 这一步把「原节点 -> 副本」的对应表编码进了结构：X 的副本恒为 X.next
        cur = head
        while cur:
            copy = Node(cur.val)
            copy.next = cur.next
            cur.next = copy
            cur = copy.next          # 跳过刚插入的副本，落到下一个原节点
        # 第二趟：靠上面的不变量接 random——Y 的副本就是 Y.next
        cur = head
        while cur:
            # random 允许为 null，不判空的话下一句会 AttributeError
            if cur.random:
                cur.next.random = cur.random.next
            cur = cur.next.next      # 每次跨过「原节点 + 副本」两个格子
        # 第三趟：拆成两条独立的链。原链必须复原，否则等于改坏了调用方的输入
        new_head = head.next
        cur = head
        while cur:
            copy = cur.next
            cur.next = copy.next     # 原链跳过副本，接回下一个原节点
            # 最后一个副本后面没有节点了，直接置 None，不能再取 .next
            copy.next = copy.next.next if copy.next else None
            cur = cur.next
        return new_head
