# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/c56f6c70fb3f4849bc56e33ff2a50b6b
# 判题: 核心代码模式
# 签名: addInList(head1: ListNode、head2: ListNode) -> ListNode

"""BM11 链表相加(二) —— 两条链先各自反转成低位在前，逐位相加带进位，结果头插回正序。

这题考什么：
    竖式加法必须**从低位开始**，而链表给的是高位在前，且单链表不能回退。
    把「取到最低位并能一路往高位走」这件事办成，题就做完了，常见有三条路：
    用栈把值压进去再弹出、把链表反转、递归到底再回溯。
    递归在 n 到 1e6 时会撞上 CPython 默认 1000 层的递归上限直接 RecursionError，
    先排除。

    这里选反转（复用 BM1 的三指针循环）：
      1. 两条链都反转，表头就成了个位；
      2. 同步向后逐位相加，`carry, digit = divmod(a + b + carry, 10)`，
         divmod 一次拿到进位和本位，比先除后模少写一遍表达式；
      3. 每算出一位就**头插**到结果链前面。头插相当于边算边把结果反回正序，
         省掉最后再反转一次；
      4. 某条链先走完就当 0 继续；循环结束时若 carry 还是 1，
         `while a or b or carry` 会再转一轮，头插出最高位的 1——
         这正是 999 + 1 = 1000 这种进位到新位数的情况，也是题面样例一。

数据规模与复杂度：
    n、m 最大到 1e6，节点值 0 <= val <= 9，其他语言时限 4 秒。
    两趟反转加一趟相加，指针操作在 3 * 1e6 量级，时间 O(n + m)、
    额外指针 O(1)（结果链的 max(n,m)+1 个新节点是必须的输出，不计入额外空间）。
    栈的写法同样 O(n) 时间，但要先把 2e6 个值压进两个列表，
    在 512M 空间限制下也能过，只是没有反转法省。

坑在哪：
  1. 反转会**改坏入参链表的结构**。判题只看返回值，所以这里无妨；
     工程上若调用方还要用原链表，就得改用栈存值的写法，或者算完再反转回去；
  2. 循环条件 `while a or b or carry` 三项缺一不可。漏掉 carry，
     样例一的 [9,3,7] + [6,3] 会输出 {0,0,0} 而丢掉最高位的 1；
     漏掉 a 或 b，两条链不等长时短的走完就停，长的高位全丢；
  3. 结果用头插（`node.next = res; res = node`）而不是尾插。相加是从低位往高位算的，
     后算出来的是更高位，必须放在更前面；尾插会得到一个整体倒过来的答案；
  4. 相加的中间量必须先加 carry 再取 divmod，顺序写反（先 divmod 再加 carry）
     会把进位算丢；
  5. 两条链都为空时循环一次不进，返回 None，即空链表。

样例复核：
    [9,3,7] + [6,3]。反转后是 7,3,9 与 3,6。
    第 1 位 7+3 = 10，进位 1、本位 0；第 2 位 3+6+1 = 10，进位 1、本位 0；
    第 3 位 9+0+1 = 10，进位 1、本位 0；此时两条链走空但 carry = 1，
    再转一轮头插出 1。结果链自前向后是 1,0,0,0，与样例一致。
"""
from typing import List, Optional


class Solution:
    def _reverse(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # BM1 的三指针反转：右侧整体求值后再赋值，一句话完成「存后路、掉头、双指针前移」
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev

    def addInList(self, head1: "Optional[ListNode]", head2: "Optional[ListNode]") -> "Optional[ListNode]":
        a = self._reverse(head1)    # 反转后表头就是个位，可以像竖式一样从低位加起
        b = self._reverse(head2)
        carry = 0
        res = None                  # 头插构建，天然得到正序结果，省掉最后一次反转
        # carry 也是循环条件：两条链都走空但仍有进位时，还要再进一轮补出最高位
        while a or b or carry:
            # 本位的和从上一位的进位起手，缺席的那条链按 0 计
            s = carry
            if a:                   # 短的那条走完就当 0，不必先补齐长度
                s += a.val
                a = a.next
            if b:
                s += b.val
                b = b.next
            carry, digit = divmod(s, 10)    # 一次拿到进位与本位
            # 结果位数可能比两条输入链都多一位，只能新建节点而不是复用原节点
            node = ListNode(digit)
            node.next = res         # 新算出的是更高位，插到最前面
            res = node
        return res
