# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/c087914fae584da886a0091e877f2c79
# 判题: 核心代码模式
# 签名: deleteDuplicates(head: ListNode) -> ListNode

"""BM15 删除有序链表中重复的元素-I —— 有序表里相同的值必然相邻，等值就把后继跳过去。

这题考什么：
    「链表中元素从小到大有序」是全题的支点：相同的值一定挤在一起，
    所以只要比较**相邻**两个节点，不需要任何记录已见值的容器。

    一个指针 cur 从表头扫：
      - `cur.val == cur.next.val`：把 cur.next 摘掉（`cur.next = cur.next.next`），
        **cur 本身不动**——新接上来的后继可能还是同一个值（如 1,1,1）；
      - 不相等：cur 前移一格。

    「删了就不前移、没删才前移」是这类原地删除的通用节奏。正因为前移不是每轮都发生，
    只能用 while，写成 for 就没有「原地再比一次」的余地了。
    链表的删除操作见 docs/ds/linked-list.md。

数据规模与复杂度：
    链表长度 0 <= n <= 100，|val| <= 100，其他语言时限 2 秒。
    每轮循环要么删掉一个节点、要么前移一格，两者合计不超过 2n 次，
    时间 O(n)、额外空间 O(1)，达到题面进阶要求。
    用 set 记录出现过的值同样是 O(n) 时间，但白白多花 O(n) 空间，
    而且丢掉了「有序」这个前提——本题的正确解法恰恰是把这个前提用足。

坑在哪：
  1. 删除之后 cur **不能**前移。1,1,1 这种连续三个相同值的输入，
     一删就前移会只摘掉中间那个，结果剩下 1,1；
  2. 循环条件是 `while cur and cur.next`：cur.next 为空说明已经到表尾，
     没有下一个可比；少判 cur.next 会在 None 上取 val；
  3. 每种值的第一个节点一定保留，表头永远不会被删，所以**不需要哑节点**，
     直接返回 head 即可。这正是它和 BM16 的分水岭——BM16 要把重复的值整组删光，
     表头可能一个不剩，就非上哑节点不可；
  4. 有序是题面给的前提，不是可以验证的推论。输入若无序，相同的值不相邻，
     这个写法会漏删，那时只能改用哈希表或先排序。

样例复核：
    {1,1,2}：cur = 第一个 1，与后继相等，摘掉第二个 1，链变成 1,2，cur 不动；
    再比 1 与 2 不等，cur 前移到 2；2.next 是 None，循环结束。
    输出 {1,2}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def deleteDuplicates(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        cur = head
        # 有序表里相同值必相邻，比一对相邻节点就够；cur.next 为空即到表尾
        while cur and cur.next:
            if cur.val == cur.next.val:
                cur.next = cur.next.next    # 摘掉重复的后继，cur 原地不动再比一次
            else:
                cur = cur.next              # 只有确认不重复才前移，否则会漏删连续重复
        return head                 # 每种值的首个节点必然保留，表头不会变，不用哑节点
