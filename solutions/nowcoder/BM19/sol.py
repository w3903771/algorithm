# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/fcf87540c4f347bcb4cf720b5b350c76
# 判题: 核心代码模式
# 签名: findPeakElement(nums: integer[]) -> integer

"""BM19 寻找峰值 —— 无序数组里返回任意一个严格大于左右相邻值的下标。

这题考什么：
    二分不要求数组全局有序，只要求「看一眼 mid 处的局部信息，就能断定答案必在某一侧」。
    这题就是这条本质的最好例子，靠的是题面给的两个约束：

      1. 相邻元素永不相等（对所有有效的 i 都有 nums[i] != nums[i+1]）；
      2. 两端之外视作负无穷（nums[-1] = nums[n] = 负无穷）。

    于是任何区间 [left, right] 都是一条**没有平地**、两头朝下的折线，
    而这样的折线内部必有峰。比较 nums[mid] 与 nums[mid+1]：

        nums[mid] < nums[mid+1]   mid 处在上坡段
            沿着右边一直走，要么升到 nums[n-1]（右邻是负无穷，它就是峰），
            要么中途转折，转折点就是峰。总之 [mid+1, right] 里一定有峰。
            ->  left = mid + 1

        nums[mid] > nums[mid+1]   mid 处在下坡段
            对称地，[left, mid] 里一定有峰（mid 自己就可能是）。
            ->  right = mid

    区间每轮至少缩短一格，收敛到 left == right 时它就是峰的下标。
    二分的边界写法对照见 docs/basic/binary-search.md。

数据规模与复杂度：
    1 <= n <= 2e5，元素取值填满 32 位有符号整数范围，时限其他语言 2 秒。
    二分 O(log n)，2e5 只需约 18 次比较，空间 O(1)。
    从左往右扫第一个下降位置是 O(n) = 2e5，本题规模下同样能过，
    但题面第 4 条明确要求 O(logN)，而且下面第 1 条说明了扫描解法带来的副作用。

坑在哪：
  1. 这是**多解题**：题面原文「数组可能包含多个峰值，在这种情况下，返回任何一个
     所在位置即可」，样例 1 的说明也写着「返回 4 的索引 1 或者 8 的索引 5 都可以」。
     所以本地不能拿样例给的下标做文本比对，仓库为它配了 SPJ（special judge，特判器）
     spj.py，按峰值定义校验返回值。
     这份二分解法在样例 [2,4,1,2,7,8,4] 上走到的是下标 5 而不是样例写的 1——
     若按样例文本死比，正确解法会被本地判成错；反过来，为了让下标恰好等于 1 而
     改写成线性扫首峰，就丢掉了 O(log n)。判题配置登记在 meta.json 的 judge。
  2. 收敛到单点的写法里，right 必须更新成 mid 而不是 mid - 1：mid 处于下坡段
     只说明它右邻更小，mid 自己完全可能就是峰，减一就把答案丢了。
     对称地 left 更新成 mid + 1 是安全的——mid 右邻更大，mid 已被证明不是峰。
  3. 循环条件是 left < right，不是 left <= right。收敛到单点的写法一旦让
     left == right 还进循环，right = mid 这条分支不再缩短区间，直接死循环。
  4. mid 取下取整，配合 left < right 可推出 mid < right，因此 nums[mid + 1]
     恒不越界，不需要额外判断；若写成上取整 (left + right + 1) // 2，
     mid 可能等于 right，nums[mid + 1] 立刻越界。
  5. n == 1 时循环一次都不进，直接返回 0：单元素两侧都是负无穷，它本身就是峰。

样例复核：
    nums = [2,4,1,2,7,8,4]，n = 7。
        [0,6]  mid=3  nums[3]=2 < nums[4]=7  ->  left=4
        [4,6]  mid=5  nums[5]=8 > nums[6]=4  ->  right=5
        [4,5]  mid=4  nums[4]=7 < nums[5]=8  ->  left=5
    返回 5，nums[5] = 8 严格大于两侧的 7 与 4，符合峰值定义，特判通过。
"""
from typing import List, Optional


class Solution:
    def findPeakElement(self, nums: List[int]) -> int:
        # 区间两端都是候选下标，收敛到单点为止；n == 1 时循环不进入，直接返回 0
        left, right = 0, len(nums) - 1
        while left < right:             # 收敛到单点，left == right 即答案
            mid = (left + right) // 2   # 下取整保证 mid < right，mid + 1 不越界
            # 只比较 mid 与它的右邻，就能判定峰落在哪一侧
            if nums[mid] < nums[mid + 1]:
                left = mid + 1          # 上坡：峰在右半，mid 已被证明不是
            else:
                right = mid             # 下坡：峰在左半，mid 自己可能就是，不能减一
        return left
