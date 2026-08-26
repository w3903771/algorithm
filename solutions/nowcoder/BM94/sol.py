# 来源: 牛客 · 面试必刷TOP101　较难
# 链接: https://www.nowcoder.com/practice/31c1aed01b394f0b8b7734de0324e00f
# 判题: 核心代码模式
# 签名: maxWater(arr: integer[]) -> long

"""BM94 接雨水问题 —— 左右双指针配两侧最大值，O(1) 空间一次扫完。

这题考什么：
    先把问题拆到「一列一列地算」这个粒度：第 i 列头顶的水位由它左右两侧的
    最高柱子中**较矮**的那个决定，

        water[i] = max(0, min(maxLeft[i], maxRight[i]) - arr[i])

    最直白的做法是先用两个数组预处理出 maxLeft 与 maxRight 再求和，
    时间 O(n)、空间 O(n)。下面这份把空间压到 O(1)。

    双指针写法：l 从左、r 从右往中间走，同时维护「已走过的左半边最大值 lmax」
    与「已走过的右半边最大值 rmax」。每轮比较两者：

        lmax < rmax:  结算 l 列，ans += lmax - arr[l]，l += 1
        否则:         结算 r 列，ans += rmax - arr[r]，r -= 1

    正确性在于：当 lmax < rmax 时，l 列真正的右侧最大值 maxRight[l] >= rmax > lmax，
    于是 min(maxLeft[l], maxRight[l]) 就等于 lmax——右边究竟有多高根本不影响结果，
    可以拿还没扫完的 lmax 直接定案。换句话说，**矮的那一边可以提前拍板**。

    手推 [3,1,2,5,2,4]：

        l=0 r=5  lmax=3 rmax=4  lmax<rmax  -> 结算 l=0：3-3=0   ans=0  l=1
        l=1 r=5  lmax=3 rmax=4             -> 结算 l=1：3-1=2   ans=2  l=2
        l=2 r=5  lmax=3 rmax=4             -> 结算 l=2：3-2=1   ans=3  l=3
        l=3 r=5  lmax=5 rmax=4  lmax>=rmax -> 结算 r=5：4-4=0   ans=3  r=4
        l=3 r=4  lmax=5 rmax=4             -> 结算 r=4：4-2=2   ans=5  r=3
        l=3 r=3  循环结束，答案 5

    与单调栈解法的分工：单调栈维护一个从底到顶**递减**的下标栈，
    每遇到比栈顶更高的柱子就弹栈，把弹出的那根当「坑底」，
    用左边的新栈顶与当前柱子夹出一个横向水槽，按 (右界 - 左界 - 1) * 高度差累加。
    它是**按行（横条）**累加，双指针是**按列（竖条）**累加，时间同为 O(n)，
    但单调栈额外要 O(n) 的栈空间、代码也更长；它的优势是能顺带回答
    「每个坑的左右边界在哪」这类需要结构信息的问题。纯求总量时双指针更划算。
    单调栈的完整写法见 docs/ds/monotonic-stack.md。

数据规模与复杂度：
    n <= 2e5，每个值满足 0 < val <= 1e9，时限「其他语言 2 秒」，题面要求 O(n)。
    双指针时间 O(n)、空间 O(1)；前缀最大值数组的写法与单调栈都是 O(n) 空间。
    题面另外保证返回结果不超过 1e9，仍在 32 位有符号整数范围内，
    签名给的 long 只是留余量；Python 的 int 是任意精度的，不存在溢出问题，
    但在 C/Java 里按题面签名用 long 是稳妥的默认选择。

坑在哪：
  1. 先更新 lmax、rmax，再做减法。顺序反了会出现 arr[l] > lmax 的时刻，
     差值为负、把水量减掉；先更新则 lmax >= arr[l] 恒成立，
     差值天然非负，也就省掉了 max(0, ...) 这一层。
  2. 结算哪一侧由 lmax 与 rmax 的比较决定，不是由 arr[l] 与 arr[r] 的比较决定。
     拿当前柱高去比会在「矮柱子挡在高墙后面」的形状上结算错边。
  3. 循环条件是 l < r 而不是 l <= r。取等时两个指针指向同一列，
     那一列会被结算两次，水量翻倍。
  4. 最左与最右两列永远接不到水（外侧视为高度 0），
     上面的式子在这两列上算出的差值恰好是 0，不必特判。
  5. 数组为空或长度 1、2 时循环立刻结束或算不出正收益，返回 0。
"""
from typing import List, Optional


class Solution:
    def maxWater(self, arr: List[int]) -> int:
        # 对撞双指针：空数组时 right = -1，循环条件先行短路，不会越界
        left, right = 0, len(arr) - 1
        lmax = rmax = 0        # 左/右半边已扫过的最高柱子，也就是各自方向的挡水墙
        ans = 0
        while left < right:    # 取 < 而非 <=：相等时两指针同列，会把那一列结算两次
            # 先把当前柱子并进各自的最大值，保证下面的差值非负，省掉 max(0, ...)
            lmax = max(lmax, arr[left])
            rmax = max(rmax, arr[right])
            # 比较的是两堵墙而不是两根柱子：矮的那一边才是短板，
            # 它的水位已经能拍板，另一边究竟多高都不会再改变结果
            if lmax < rmax:
                ans += lmax - arr[left]
                left += 1
            else:
                ans += rmax - arr[right]
                right -= 1
        return ans
