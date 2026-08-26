# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/e016ad9b7f0b45048c58a9f27ba618bf
# 判题: 核心代码模式
# 签名: findKth(a: integer[]、n: integer、K: integer) -> integer

"""BM47 寻找第K大 —— 快速选择：每轮只在 partition 后包含目标下标的那一半继续切，期望 O(n)。

这题考什么：
    题目点名「根据快速排序的思路」，即快速选择（quickselect）。
    快排每次 partition 之后，pivot 就落到了它排好序时该在的位置上；
    既然只关心第 K 大这**一个**位置，另外半边根本不用排——
    只往包含目标下标的那一侧继续切，就把 O(n log n) 降成期望 O(n)。

    这里按**降序**划分（大的在左），目标就是下标 K-1：

      1. 随机选一个 pivot，做三路划分，把区间切成 [ >pivot | ==pivot | <pivot ]；
      2. 若 K-1 落在中间那段，pivot 就是答案，直接返回；
      3. 否则只在左段或右段里继续找。

    循环不变量：目标下标 target 始终落在当前区间 [lo, hi] 内，
    而每一轮区间都严格变短，所以循环一定会停在中段上。

数据规模与复杂度：
    0 <= n <= 1000，1 <= K <= n，0 <= val <= 1e7，时限「其他语言 2 秒」。
    每轮 partition 扫一遍当前区间，随机 pivot 使区间期望减半，
    n + n/2 + n/4 + ... < 2n，故期望 O(n)；最坏 O(n^2) = 1e6，本规模下也扛得住。
    空间 O(1)：全程在原数组上交换，除几个下标变量外不开新空间——
    这正是题面对空间的要求，排序后取下标的写法虽然更短，却要额外的 O(n) 或改动整个数组。

坑在哪：
  1. 三路划分不是装饰。经典二路划分把「等于 pivot」的元素固定分到某一侧，
     全相等的数组每轮只能切掉一个元素，直接退化成 O(n^2)；
     示例 2 的 [10,10,9,9,8,7,5,6,4,3,4,2] 就带重复值。
     三路把等于 pivot 的一整段一次性归位，重复再多也只扫一遍。
  2. 随机 pivot 防的是另一类数据：固定取首元素或尾元素时，
     已经有序的输入每轮同样只能切掉一个元素，同样退化。
  3. 本题要的是**不去重**的第 K 大：示例 2 说明里写得很清楚，
     去重后的第 3 大是 8，但正确答案是 9。按下标 K-1 取而不是按去重后的名次取，天然满足。
  4. 划分按降序排布，目标下标才是 K-1；若改成升序划分，第 K 大对应的下标是 n-K，
     两者混用会稳定地差几位。
  5. 三路划分里，把小元素换到右边之后，从 gt 处换过来的那个元素**还没检查过**，
     所以 i 不能前进；三个分支中只有这一支不推进 i，写成推进会漏判一个元素。

样例复核：
    [1,3,5,2,2] 求第 3 大，target = 2。降序排好是 5,3,2,2,1，下标 2 上是 2，
    与示例 1 的答案一致；快速选择不必真的排完，只要某轮的等值中段覆盖下标 2 即可返回。
"""
import random
from typing import List, Optional


class Solution:
    def findKth(self, a: List[int], n: int, K: int) -> int:
        # 迭代而非递归：每轮把搜索区间收缩到含 target 的那一侧，栈深恒为 1
        lo, hi = 0, len(a) - 1
        target = K - 1                       # 降序排列后，第 K 大就在下标 K-1
        # 循环不变量：target 始终落在 [lo, hi] 内，且区间每轮严格变短，故必然终止
        while True:
            lt, gt = self._partition(a, lo, hi)
            if target < lt:                  # 目标在「大于 pivot」的左段
                hi = lt - 1
            elif target > gt:                # 目标在「小于 pivot」的右段
                lo = gt + 1
            else:                            # 落在等于 pivot 的中段，答案就是 pivot
                return a[target]

    @staticmethod
    def _partition(a: List[int], lo: int, hi: int):
        """三路划分（降序）：返回等于 pivot 的区间 [lt, gt]。

        划分结束后 a[lo:lt] > pivot、a[lt:gt+1] == pivot、a[gt+1:hi+1] < pivot。
        重复元素一次性全部归位，避免全相等数组退化成 O(n^2)。
        """
        pivot = a[random.randint(lo, hi)]    # 随机 pivot，防有序输入退化
        # 四段结构：[lo,lt) 大于 pivot、[lt,i) 等于、[i,gt] 待定、(gt,hi] 小于
        # i 是扫描游标，lt 与 gt 是两段已定区间的边界
        lt, i, gt = lo, lo, hi
        # 待定区间为空即划分完毕
        while i <= gt:
            if a[i] > pivot:                 # 大的甩到左边
                a[lt], a[i] = a[i], a[lt]
                lt += 1
                i += 1
            elif a[i] < pivot:               # 小的甩到右边；换过来的元素还没看过，i 不前进
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt
