# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/f23604257af94d939848729b1a5cda08
# 判题: 核心代码模式
# 签名: sortInList(head: ListNode) -> ListNode

"""BM12 单链表的排序 —— 把值取出来交给 C 层的 Timsort 排好，再按序写回原节点。

这题考什么：
    题面允许空间复杂度 O(n)、要求时间 O(n log n)，这两条合起来就把「必须写链表归并」
    的必要性取消了。既然可以用 O(n) 空间，最省事也最快的路径是：
      1. 一趟遍历把所有 val 收进列表；
      2. `list.sort()`——CPython 的 Timsort（归并与插入排序的混合，全程在 C 层跑，
         排序算法见 docs/basic/sorting.md）；
      3. 再一趟遍历按顺序写回各节点的 val。

    节点对象和 next 指针一个都没动，只换了值，所以根本不存在断链风险，
    返回的还是原来的表头。**把排序的活交给 C 层**是 Python 刷题的通用套路：
    Python 层每做一次比较都要走一遍属性访问和解释器循环，
    而 Timsort 的比较发生在 C 里，两者常数差着一个数量级。

    若面试明确要求 O(1) 空间，就走**自底向上的归并排序**：step 从 1 开始翻倍，
    每轮把相邻两段长 step 的有序块用 BM4 的 merge 合并，直到 step >= n。
    递归版归并（快慢指针找中点后分治）在 n = 1e5 时深度只有 17 层，不会爆栈，
    但栈空间是 O(log n)，算不上真正的 O(1)。

数据规模与复杂度：
    0 < n <= 100000，节点权值在 [-1e9, 1e9]，其他语言时限 4 秒。
    收值、排序、写回三趟合计 O(n log n) 时间、O(n) 空间，正好卡在题面允许的范围里。
    冒泡或选择排序是 n 的平方，1e5 的平方是 1e10 次比较，纯 Python 下要跑上小时级，
    连 C 语言都过不了。

坑在哪：
  1. 只改 val、不动 next，所以链表结构原封不动，返回 head 即可；
     若改成重接指针的写法，就必须小心把最后一个节点的 next 收成 None，否则成环；
  2. 写回的循环用 `for v in vals` 配一个同步前进的指针，两者步数天然相等——
     列表长度就是链表长度，不会出现越界或漏写；
  3. 节点值可以是负数（题面给到 -1e9），任何「用 0 当哨兵」「按非负假设开桶」的
     写法都会错；
  4. n 至少为 1（题面写的是 0 < n），但 vals 为空时循环也不进、直接返回 head，
     判题环境送空链表进来也不会崩。

样例复核：
    [1,3,2,4,5]：收值得 [1,3,2,4,5]，排序后 [1,2,3,4,5]，
    按原节点顺序写回，链表变成 {1,2,3,4,5}，与样例一致。
"""
from typing import List, Optional


class Solution:
    def sortInList(self, head: "Optional[ListNode]") -> "Optional[ListNode]":
        # 第一趟：只收值不动结构，链表顺序与列表下标一一对应
        vals = []
        p = head
        while p:
            vals.append(p.val)
            p = p.next
        vals.sort()                 # Timsort 在 C 层跑，比 Python 手写链表归并快一个数量级
        # 第二趟：按序写回。列表长度等于链表长度，两个游标同步推进不会越界
        p = head
        for v in vals:
            p.val = v
            p = p.next
        return head                 # 指针结构全程没动，原表头仍是新表头
