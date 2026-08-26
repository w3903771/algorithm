# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/9f3231a991af4f55b95579b44b7a01ba
# 判题: 核心代码模式
# 签名: minNumberInRotateArray(nums: integer[]) -> integer

"""BM21 旋转数组的最小数字 —— 拿 nums[mid] 与右端点比，相等时只能保守地把右端点退一格。

这题考什么：
    旋转后的数组是「两段各自非降序」的拼接，最小值就是第二段的开头，也就是旋转点。
    数组整体无序，但「mid 落在哪一段」这个局部判断足以排除一半区间，于是仍能二分。

    比较对象必须选**右端点** nums[right]：

        nums[mid] > nums[right]
            左段的每个数都不小于右段的每个数，mid 只能在左段，
            旋转点严格在 mid 右侧  ->  left = mid + 1

        nums[mid] < nums[right]
            mid 落在右段，它自己就可能是最小值  ->  right = mid

        nums[mid] == nums[right]
            局部信息不足以判别，见下面「坑在哪」第 2 条  ->  right 退一格

    循环用 left < right 收敛到单点，返回 nums[left]。
    二分的两套边界模板见 docs/basic/binary-search.md。

数据规模与复杂度：
    1 <= n <= 10000，元素取值 0 到 10000，时限其他语言 2 秒。
    题面说的是「非降序数组」旋转，所以**允许重复元素**，示例 2 的 [3,100,200,3]
    首尾就相等。
    平均 O(log n)，全部元素相等时退化到 O(n) = 1e4 次比较，这个规模下毫无压力；
    空间 O(1)，正是题面要求的两项。

坑在哪：
  1. 不能与左端点比。完全没有旋转的 [1,2,3,4,5]，nums[mid] = 3 大于 nums[left] = 1，
     按「mid 在左段」的规则会往右走，直接错过下标 0 上的最小值。
     与右端点比就没有这个问题：此时 nums[mid] < nums[right]，区间正确地向左收。
  2. nums[mid] == nums[right] 时**只能退一格，不能二分**。两个反例长得一模一样：

         [1, 0, 1, 1, 1]   最小值在 mid 左侧
         [1, 1, 1, 0, 1]   最小值在 mid 右侧

     两者的 nums[mid] 与 nums[right] 都等于 1，凭这个比较结果丢掉任何一半都可能
     把最小值丢掉。right 减一是安全的保守做法：nums[right] 与 nums[mid] 相等，
     即使 right 本身是最小值，mid 处还留着同样的值，答案不会丢。
     代价是全等数组退化到 O(n)——有重复元素时这个代价无法避免。
  3. nums[mid] < nums[right] 分支里 right 只能取 mid，不能取 mid - 1。
     mid 落在右段，它自己就可能是旋转点，减一就把答案排除了。
  4. 循环条件是 left < right。写成 left <= right 时，left == right 的那一轮
     mid 等于 left，right = mid 不缩短区间，直接死循环。

样例复核：
    [3,100,200,3]（示例 2，首尾相等）：
        [0,3]  mid=1  nums[1]=100 > nums[3]=3  ->  left=2
        [2,3]  mid=2  nums[2]=200 > nums[3]=3  ->  left=3
    返回 nums[3] = 3，与样例一致。

    [1,0,1,1,1]（重复元素的最坏形态）：
        [0,4]  mid=2  nums[2]=1 == nums[4]=1   ->  right=3
        [0,3]  mid=1  nums[1]=0 <  nums[3]=1   ->  right=1
        [0,1]  mid=0  nums[0]=1 >  nums[1]=0   ->  left=1
    返回 nums[1] = 0，退一格没有丢掉答案。
"""
from typing import List, Optional


class Solution:
    def minNumberInRotateArray(self, nums: List[int]) -> int:
        # 收敛到单点，left == right 时它就是旋转点；比较对象固定为右端点 nums[right]
        left, right = 0, len(nums) - 1
        while left < right:
            mid = (left + right) // 2
            # 三分支：mid 在左段 / mid 在右段 / 值相等无法判别
            if nums[mid] > nums[right]:
                left = mid + 1          # mid 在左段，旋转点严格在右侧
            elif nums[mid] < nums[right]:
                right = mid             # mid 在右段，它自己可能就是最小值，不能减一
            else:
                right -= 1              # 值相等无从判别，只丢掉一个重复候选，答案仍在区间内
        return nums[left]               # 区间收敛到单点
