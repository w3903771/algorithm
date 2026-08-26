"""LC34 在排序数组中查找元素的第一个和最后一个位置 —— 两次「下界」二分把 target 的一段夹出来。

这题考什么：
    数组非递减，所以等于 target 的元素必定挤在**一段连续区间**里。
    求这段区间的左右端点，只需要一个基本件：下界二分

        lower(t) = 满足 nums[k] >= t 的最小下标 k；不存在时返回 n。

    这就是标准库 bisect_left 的语义，模板见 docs/basic/binary-search.md 的 44.2 节
    写法一，本题解在函数内实现了一份。有了它，两个端点都是一行：

        起点 first = lower(target)
        终点 last  = lower(target + 1) - 1

    第二个式子是全题的关键。lower(target + 1) 是第一个 **> target** 的下标
    （元素都是整数，「>= target + 1」与「> target」等价），它左边紧挨着的那一个
    就是最后一个等于 target 的位置。这样两次二分用的是**同一个**函数，
    不必再手写一份容易写错的上界二分（上界模板要把 mid 改成上取整，见 44.2 写法二）。

    存在性判断也由 first 一并给出：lower(target) 返回的是第一个 >= target 的位置，
    若这个位置越界或它上面的值不等于 target，就说明数组里根本没有 target。
    这两个条件缺一不可，而且顺序不能反——先判越界再取值。

数据规模与复杂度：
    0 <= nums.length <= 1e5（**可以是空数组**，样例 3 就是），
    元素与 target 都在 [-1e9, 1e9]，数组非递减。
    时间 O(log n)：两次二分，每次至多 17 轮（2 的 17 次方 > 1e5）。
    空间 O(1)。
    线性扫一遍统计首末位置是 O(n)，n = 1e5 时也能过，但题面要求 O(log n)。

坑在哪：
  1. 空数组必须能跑通。本题解不需要为它写特判：len(nums) 为 0 时二分区间
     [0, 0) 一开始就是空的，循环一轮都不进，first = 0，随即被
     `first == len(nums)` 拦下，返回 [-1, -1]。若把这个判断写成
     `nums[first] != target` 打头，空数组上会立刻 IndexError。
  2. 存在性判断的两个条件顺序不能换。Python 的 or 是短路求值，
     `first == len(nums) or nums[first] != target` 里越界判断在前，
     后半句才不会去访问不存在的下标。写反就是越界。
  3. `lower(target + 1) - 1` 里的减一不能省。lower 返回的是第一个 **大于**
     target 的位置，它本身不属于答案区间；漏掉减一，nums = [5,7,7,8,8,10]、
     target = 8 会返回 [3,5]，而 nums[5] = 10 根本不是 8。
  4. target + 1 这个技巧只在元素为整数时成立。若值域是浮点数，
     「>= target + 1」与「> target」不再等价，那时必须换成真正的上界二分。
     本题元素都是整数，可以放心用。
  5. 找不到时返回 [-1, -1] 而不是空列表，也不是 [0, -1] 这类空区间记法。
     题面点名了这个返回值，判题按结构严格比对，写别的形状直接不过。
  6. 两次二分都要在**原数组**上做。有人会先二分出 first，再在 nums[first:]
     上找终点——切片本身就是 O(n) 复制，n = 1e5 时把 O(log n) 拖回 O(n)，
     而且得到的下标还要加回 first 才对应原数组，平白多一处偏移。

样例复核：
    nums = [5,7,7,8,8,10]、target = 8：
        lower(8)：第一个 >= 8 的下标是 3（nums[3] = 8），first = 3，
                  3 < 6 且 nums[3] == 8，target 存在；
        lower(9)：第一个 >= 9 的下标是 5（nums[5] = 10），last = 5 - 1 = 4。
        返回 [3, 4]，与样例一致。
    target = 6：lower(6) = 1，nums[1] = 7 不等于 6，返回 [-1, -1]，与样例一致。
    nums = []、target = 0：lower(0) = 0 == len(nums)，返回 [-1, -1]，与样例一致。
"""
from typing import List, Optional


class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        def lower(t: int) -> int:
            """返回第一个 >= t 的下标；数组里全都 < t 时返回 len(nums)。"""
            # 左闭右开区间 [left, right)。不变量：left 左边全部 < t，
            # right 及其右边全部 >= t；答案夹在这段未定区间里
            left = 0
            # 右端取 n 而非 n - 1：多出的这一格代表「不存在 >= t 的元素」。
            # 数组为空时区间一开始就是空的，循环不执行，直接返回 0
            right = len(nums)
            # left == right 时区间为空，分界线已被夹住
            while left < right:
                # 下取整保证 left <= mid < right，两支都能让区间严格缩短
                mid = (left + right) // 2
                if nums[mid] < t:
                    # mid 及其左边全部 < t，整段排除
                    left = mid + 1
                else:
                    # nums[mid] >= t，mid 自己就是候选；右开区间里 right 记的是
                    # 「已知的最小满足位置」，赋成 mid 是登记而不是丢弃
                    right = mid
            return left

        # 第一次二分：target 若存在，它的起点就是第一个 >= target 的位置
        first = lower(target)
        # 存在性判断。两个条件的顺序靠 or 的短路求值保命：先确认 first 没越界，
        # 才敢去取 nums[first]。空数组走的正是前半句
        if first == len(nums) or nums[first] != target:
            return [-1, -1]
        # 第二次二分复用同一个函数：元素都是整数，「>= target + 1」等价于「> target」，
        # 于是 lower(target + 1) 是第一个大于 target 的位置，它左边紧挨着的就是终点。
        # 减一不能省，否则返回的下标上放的已经不是 target 了
        last = lower(target + 1) - 1
        return [first, last]
