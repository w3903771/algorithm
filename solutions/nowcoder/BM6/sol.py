# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/650474f313294468a4ded3ce0f7898b9
# 判题: 核心代码模式
# 签名: hasCycle(head: ListNode) -> boolean

"""BM6 判断链表中是否有环 —— 快慢指针，快的每次两步，追上就是有环。

这题考什么：
    Floyd 判圈算法（龟兔赛跑，用两个不同速度的指针在链上跑来检测环）。
    slow 一次一步、fast 一次两步：

      - 无环：链有尽头，fast 先跑到 None，循环退出，返回 False；
      - 有环：两个指针先后进环，之后 fast 相对 slow 每轮**逼近 1 步**。
        相对位移每轮恰好减 1，就不可能「跨过去错开」，环长有限，
        所以一定在有限步内落到同一个节点上。

    用哈希表记下访问过的节点同样能判，但那是 O(n) 空间，
    题面要求空间复杂度 O(1)。双指针的更多用法见 docs/basic/two-pointer.md。

数据规模与复杂度：
    链表长度 n <= 10000，|val| <= 100000，其他语言时限 2 秒。
    无环时 fast 走 n/2 轮到头，有环时 slow 进环后最多再绕一圈就被追上，
    总步数不超过 2n，时间 O(n)、额外空间 O(1)。
    n 只有一万，哈希表法其实也跑得动，但它需要 n 个节点的 set，
    不满足题面的空间要求，而且在「只给指针、不允许额外内存」的面试语境里直接出局。

坑在哪：
  1. **本题的输入是两段**：`{3,2,0,-4},1`，第一段是链表，第二段是环入口的下标
     （-1 表示无环），环是后台按这个下标把尾节点接回去形成的。函数签名里只有一个
     head，读不到第二段，所以离开牛客后台自己造数据时必须手工把环接上，
     本仓库的复现见 driver.py。只按第一段建一条直链，
     正例永远判不出环；
  2. 循环条件必须是 `fast and fast.next`。只判 fast 非空的话，
     fast 停在最后一个节点时 `fast.next.next` 会在 None 上取属性抛 AttributeError；
  3. slow 和 fast 都从 head 出发，起点相同，但比较写在两个指针移动**之后**，
     所以第 0 步的「相遇」不会被误判成有环；
  4. 判相等用 `is` 而不是 `==`。要的是「同一个节点对象」，
     题面允许节点值重复（|val| <= 100000 里没有互异的保证），值相等不代表转回了原处。

样例复核：
    {1},-1 是一个孤立节点：fast = head，fast.next 是 None，while 一次都不进，返回 False。
    {3,2,0,-4},1 把 -4 接回下标 1 的节点：slow 依次走到 2、0、-4，
    fast 依次走到 0、2、-4，第 3 轮两者同时落在 -4 上，返回 True，与样例一致。
"""
from typing import List, Optional


class Solution:
    def hasCycle(self, head: "Optional[ListNode]") -> bool:
        # 同一起点出发；比较放在移动之后，所以起点相同不会被当成相遇
        slow = fast = head
        while fast and fast.next:   # fast 要走两步，这两个都得非空才不会取空属性
            slow = slow.next
            fast = fast.next.next
            if slow is fast:        # 相对速度恰好 1，有环必然某轮落到同一节点
                return True
        return False                # fast 撞到链尾，说明链有尽头，无环
