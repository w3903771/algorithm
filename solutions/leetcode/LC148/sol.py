"""LC148 排序链表 —— 给定链表头，把它按 val 升序重排后返回新表头。

这题考什么：
    链表不能随机访问，快速排序那种「按下标取 pivot、左右交换」的套路用不上，
    但**归并排序**天生适合链表：合并两条有序链只需要改 next 指针，
    不像数组归并那样要开一个等长的临时数组。归并排序本身见
    docs/basic/sorting.md，两条链的合并就是 LC21。

    进阶要求常数空间，于是取**自底向上**（迭代）的归并，而不是自顶向下的递归：

        width = 1, 2, 4, 8, ...
        每一轮从头扫一遍，把相邻的两个长度为 width 的有序块合成一个 2*width 的块

    width = 1 时每个单节点自成有序块，扫完一轮所有相邻两节点都排好；
    width 每轮翻倍，做 ceil(log2 n) 轮之后整条链只剩一个块，排序完成。

    实现上拆成两个辅助方法：
      _split(node, size)  从 node 起切下 size 个节点（把第 size 个的 next 置 None），
                          返回剩下那段的头，供下一次切割；
      _merge(prev, a, b)  合并两条有序链并接在 prev 后面，返回合并后这一段的**尾节点**，
                          它正是下一对块的 prev。
    靠这个返回的尾节点，外层不用回头去找接点，整轮扫描保持 O(n)。

数据规模与复杂度：
    节点数最多 5 * 10^4，值域 -10^5..10^5。
    时间 O(n log n)：ceil(log2 5*10^4) = 16 轮，每轮扫过全部节点，
    约 16 * 5 * 10^4 = 8 * 10^5 次指针操作。额外空间 O(1)，只有几个游标。

    对照两条被否决的思路：
    - 插入排序建链（LC147 的做法）是 O(n^2)，最坏 (5*10^4)^2 = 2.5 * 10^9 次比较，
      Python 下没有任何过的可能；
    - 把 val 收进列表、`sorted` 之后写回，时间同样 O(n log n) 而且常数极小
      （sorted 是 C 实现），但要多开 5 * 10^4 个元素的列表，空间 O(n)，
      正是进阶要排除的做法。

坑在哪：
  1. `_split` 必须真的**断链**（把左块最后一个节点的 next 置 None）。不断的话
     _merge 里的 `while a and b` 会顺着原链一路走下去，把本该属于后面块的节点
     也卷进这次合并，结果乱序；
  2. `_merge` 要返回合并段的尾节点。返回头节点的话，外层每一对都得重新遍历
     去找接点，一轮就从 O(n) 退化成 O(n^2)；
  3. 外层循环条件是 `width < n`，不是 `width <= n`。写成 `<=` 会在 n 恰好是
     2 的幂时多跑一轮空转（此时整条链已是单个有序块）；
  4. 长度必须先量出来。不量长度就不知道什么时候停，而「扫一轮没发生合并就停」
     这类判据在链表上并不好写；
  5. 空链与单节点自动落到 `width < n` 不成立，直接返回原 head，对应样例三的 []；
  6. 比较用 `<=` 保证稳定排序。本题只比 val 看不出区别，但同一套 _merge
     用在带附加字段的节点上时，`<` 会打乱相等元素的原有次序。

样例复核：
    [4,2,1,3]，n = 4。
    width = 1：切出 (4)(2) 合成 2 -> 4；再切出 (1)(3) 合成 1 -> 3。链变为 2 -> 4 -> 1 -> 3。
    width = 2：切出 (2,4)(1,3) 合成 1 -> 2 -> 3 -> 4。
    width = 4 不小于 n，退出。返回 [1,2,3,4]，与样例一致。
"""
from typing import List, Optional


class Solution:
    def sortList(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # 先量长度：自底向上归并要按块长 1,2,4,... 逐轮扫，得知道什么时候扫完
        n = 0
        node = head
        while node:
            n += 1
            node = node.next
        # 哨兵固定住表头。每轮合并都可能换掉真正的第一个节点，有它就不用另外记
        dummy = ListNode(0)
        dummy.next = head
        width = 1
        # width 每轮翻倍；等于或超过 n 时整条链已经是单个有序块
        while width < n:
            prev = dummy             # prev 始终是「本轮已排好的前缀」的最后一个节点
            cur = dummy.next         # cur 是本轮还没处理的第一个节点
            while cur:
                left = cur
                right = self._split(left, width)   # 切下左块，返回右块的头
                cur = self._split(right, width)    # 切下右块，返回下一对的头
                prev = self._merge(prev, left, right)
            width *= 2
        return dummy.next            # 表头在合并中会变，只能从哨兵取

    def _split(self, node: "Optional[ListNode]", size: int) -> "Optional[ListNode]":
        """从 node 起切下 size 个节点自成一条链，返回剩下那段的头。

        走 size - 1 步是因为起点 node 本身已经算第一个；中途撞到 None
        说明这一块不足 size 个，后面没有剩余，返回 None。
        """
        for _ in range(size - 1):
            if node is None:
                break
            node = node.next
        if node is None:
            return None
        rest = node.next
        node.next = None             # 断链：左块必须以 None 结尾，_merge 才知道在哪停
        return rest

    def _merge(self, prev: "ListNode", a: "Optional[ListNode]",
               b: "Optional[ListNode]") -> "ListNode":
        """把两条有序链合并后接在 prev 之后，返回合并段的**尾节点**。

        返回尾节点是为了让外层直接拿它当下一对块的 prev，
        免去每对都回头找接点造成的重复遍历。
        """
        cur = prev
        while a and b:
            # 相等取 a，保持稳定：原本靠前的相等元素仍然靠前
            if a.val <= b.val:
                cur.next = a
                a = a.next
            else:
                cur.next = b
                b = b.next
            cur = cur.next
        # 剩下那条整段有序且不小于已接出的部分，一次接上
        cur.next = a if a else b
        # cur 此刻停在接口处，把它推到这一段真正的末尾再交给外层
        while cur.next:
            cur = cur.next
        return cur
