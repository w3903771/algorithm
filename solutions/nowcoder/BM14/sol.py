# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/02bf49ea45cd486daa031614f9bd6fc3
# 判题: 核心代码模式
# 签名: oddEvenList(head: ListNode) -> ListNode

"""BM14 链表的奇偶重排 —— 就地拆成奇数位、偶数位两条链，最后把偶链接到奇链尾巴上。

这题考什么：
    题意是按**位置编号**分组（第 1、3、5... 个归一组），不是按节点值的奇偶，
    题面专门强调了「注意是节点的编号而非节点的数值」。

    做法是「原地拆链再拼接」，一趟走完：

        odd  = head          奇数位链的尾指针，从第 1 个开始
        even = head.next     偶数位链的尾指针，从第 2 个开始
        even_head = even     记住偶链的表头，最后要接上去

    每轮让两个尾指针各自越过一个异类节点，跳到自己组的下一个：

        odd.next  = even.next;  odd  = odd.next
        even.next = odd.next;   even = even.next

    循环不变量是「odd 和 even 分别是两条子链当前的最后一个节点，
    且 even 正好排在 odd 的后一位」。收尾一句 `odd.next = even_head` 把两条链缝起来。
    链表的拆分与拼接见 docs/ds/linked-list.md。

数据规模与复杂度：
    节点数 0 <= n <= 1e5（题面备注给的上界是 200000），节点值在 [0, 1000]，
    其他语言时限 2 秒。每个节点只被重接一次，时间 O(n)、额外空间 O(1)，
    优于题面要求的 O(n) 空间。
    先扫两遍分别收集奇偶位再重建链同样是 O(n)，但要多存两个列表，
    在链表这种「指针本来就能随意接」的结构上没有必要。

坑在哪：
  1. 循环条件 `while even and even.next` 两个判断缺一不可：
     even 为 None 说明偶链已经到尾（节点数为奇数的情形），
     even.next 为 None 说明后面没有下一个奇数位了（节点数为偶数的情形）。
     少判前者，`even.next` 会在 None 上取属性；少判后者，
     `odd.next` 会拿到 None 再取 next 而崩；
  2. 四句赋值的顺序不能调换。必须先把 odd 推到新的奇数位，
     才能用 `odd.next` 取到下一个偶数位；先动 even 就取不到正确的后继了；
  3. 拼接后不会成环：循环退出时 even 侧要么是 None，
     要么它的 next 本来就是 None（最后一个节点），偶链尾已经天然收口，
     所以 `odd.next = even_head` 之后整条链仍以 None 结束；
  4. 空链表和单节点必须先挡掉。head.next 是 None 时 even 就是 None，
     后面 `even_head` 与循环都无从谈起，直接返回原表。

样例复核：
    {1,2,3,4,5,6}：odd = 1、even = 2。
    第一轮 1 接 3、2 接 4，odd = 3、even = 4；第二轮 3 接 5、4 接 6，odd = 5、even = 6。
    此时 6.next 是 None，循环退出，5 接上偶链头 2，
    得到 {1,3,5,2,4,6}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def oddEvenList(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # 不足两个节点时没有偶数位可分，直接原样交回，也避开后面的空指针
        if head is None or head.next is None:
            return head
        odd = head                  # 奇数位链的尾
        even = head.next            # 偶数位链的尾，恒排在 odd 的后一位
        even_head = even            # 偶链头要留到最后拼接，先存下来
        # even 为空表示偶链到尾，even.next 为空表示后面没有奇数位了，两者都得判
        while even and even.next:
            odd.next = even.next    # even.next 就是下一个奇数位
            odd = odd.next
            even.next = odd.next    # 顺序不能换：先推 odd 才取得到下一个偶数位
            even = even.next
        odd.next = even_head        # 奇链尾接偶链头；偶链尾此时已指向 None，不会成环
        return head
