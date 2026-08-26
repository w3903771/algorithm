# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/3fed228444e740c8be66232ce8b87c2f
# 判题: 核心代码模式
# 签名: isPail(head: ListNode) -> boolean

"""BM13 判断一个链表是否为回文结构 —— 快慢指针找中点，反转后半段再与前半段对撞比较。

这题考什么：
    最省事的写法是把值全收进列表再判 `vals == vals[::-1]`，O(n) 空间也能过。
    但这题真正要练的是 **O(1) 空间**的三步走，正好把前面几题的零件拼起来：

      1. **找中点**：快慢指针，fast 一次两步、slow 一次一步。
         fast 撞到 None（偶数个节点）或停在最后一个节点（奇数个）时，slow 落在中点；
      2. **反转后半段**：从 slow 开始做 BM1 的三指针反转，prev 成为后半段的新表头；
      3. **对撞比较**：一个指针从原表头出发，一个从反转后的新表头出发，逐个比 val。

    循环条件 `while fast and fast.next` 决定了 slow 的落点：n 为偶数时 slow 停在
    后半段的第一个节点，后半段长 n/2；n 为奇数时停在正中间，后半段长 (n+1)/2，
    正中那个节点两边都会走到，自己和自己比恒相等，不影响结论。
    两种情况下后半段都不比前半段长，所以用「后半段走空」当终止条件是安全的。
    双指针技巧见 docs/basic/two-pointer.md。

数据规模与复杂度：
    链表节点数 n <= 1e5，|val| <= 1e7，其他语言时限 2 秒。
    找中点 n/2 步、反转 n/2 步、比较 n/2 步，时间 O(n)、额外空间 O(1)。
    收值进列表再切片比较同样是 O(n) 时间，但要多存 1e5 个整数，
    在「链表长到装不下」的语境里就不成立了，本解法不依赖这个前提。

坑在哪：
  1. 反转后半段会**改坏原链表**（后半段方向反了，前半段末尾还指着后半段的原首节点）。
     判题只取返回值，所以无所谓；工程上若要求不破坏输入，比完再把后半段反转回去；
  2. 对撞循环必须以后半段的指针 q 为准（`while q`）。后半段被反转后以 None 结束，
     而前半段的末尾还指着接缝之后的节点，以 p 为准会在 q 已经走空之后继续读 q.val，
     在 None 上取属性直接崩；
  3. 找中点的条件写成 `while fast.next and fast.next.next` 会让 slow 停在前半段的
     末尾，后半段反而变长，此时以 q 为终止条件就会越过接缝；两个写法的落点差一位，
     必须和第 3 步的终止条件配套；
  4. 比较用 `!=` 比的是 val 不是节点。回文判的是值序列，
     前后两半本来就是不同的节点对象；
  5. n <= 1 时直接返回 True：空链表和单节点都是回文，
     提前退出还省掉了后面在 None 上取属性的判断。

样例复核：
    {2,1} 不是回文：slow 从 2 走一步到 1，fast 走两步到 None，后半段是 1。
    反转后 q 从 1 开始，p 从 2 开始，第一次比较 2 != 1，返回 False，与样例二一致。
"""
from typing import List, Optional


class Solution:
    def isPail(self, head: "Optional[ListNode]") -> bool:
        # 空表和单节点必然回文；提前退出也免去了后面 head.next 的空判断
        if head is None or head.next is None:
            return True
        # 1) 快慢指针找中点：偶数时 slow 停在后半段首个，奇数时停在正中间
        slow, fast = head, head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        # 2) 反转后半段，prev 成为后半段的新表头
        prev = None
        while slow:
            slow.next, prev, slow = prev, slow, slow.next
        # 3) 对撞比较。以 q（后半段）走空为终止：它的长度不超过前半段，
        #    换成 p 会越过接缝去读已经改向的指针
        p, q = head, prev
        while q:
            if p.val != q.val:      # 比的是值，前后两半本来就是不同的节点对象
                return False
            p, q = p.next, q.next
        return True
