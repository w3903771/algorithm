"""LC33 搜索旋转排序数组 —— 每轮先判断 mid 落在哪一段，那一段是有序的，据此决定往哪半边走。

这题考什么：
    旋转后的数组整体无序，但它有很强的结构：它是**两段各自升序**的拼接，
    并且左段的每个数都大于右段的每个数（元素互不相同，所以是严格大于）。

        [4,5,6,7 | 0,1,2]
         左段升序  右段升序，且左段最小的 4 > 右段最大的 2

    二分的前提是「能用一次比较排除一半」。整体不单调，看起来用不了二分，
    但关键观察是：任取一个 mid，把区间 [left, right] 切成 [left, mid] 与 [mid, right]，
    **至少有一段是完整有序的**——因为断点只有一个，它最多落在其中一段里。
    只要认出那段有序的，就能判断 target 在不在它的值域范围内：

        在  -> 答案只可能在这一段，往这边收；
        不在 -> 答案只可能在另一段，往那边收。

    两种情形都排除掉了一半，于是复杂度仍是 O(log n)。

    「哪一段有序」用 nums[left] <= nums[mid] 判断：成立说明 left 到 mid 之间
    没有跨过断点，左半有序；否则断点在左半，右半必定有序。
    这里用 <= 而不是 <，是为了照顾 left == mid 的情形（区间只剩一两个元素时会发生），
    此时左半只有一个元素，当然算有序。

    本题解用二分的写法三（闭区间 + 命中即返回），
    见 docs/basic/binary-search.md 的 44.2 节。

数据规模与复杂度：
    1 <= nums.length <= 5000，元素与 target 都在 [-1e4, 1e4]，
    元素**互不相同**，且题目保证数组确实是某次旋转的结果（含旋转 0 位的原数组）。
    时间 O(log n)：n = 5000 时至多 13 轮。空间 O(1)。
    直接 `target in nums` 或线性扫描是 O(n)，5000 的规模跑得动，
    但题面明确要求 O(log n)。

坑在哪：
  1. 「元素互不相同」是本题能一次二分到底的**前提**，不是可有可无的描述。
     对照牛客 BM21 旋转数组的最小数字：那题是非降序数组旋转，**允许重复**，
     于是会出现 nums[left] == nums[mid] == nums[right] 却分不清断点在哪的局面
     （比如 [1,1,1,0,1]），只能把端点保守地退一格，最坏退化成 O(n)。
     本题没有重复元素，nums[left] <= nums[mid] 这一条判断永远给得出确定答案。
  2. 判定有序的那一半时，比较的是 nums[left] 与 nums[mid]，不是 nums[mid] 与
     nums[right]。两种写法都能做，但**分支条件要成套换**，混着写必错。
  3. 范围判断的两侧开闭要分清：左半有序时用 nums[left] <= target < nums[mid]，
     右端是开的（nums[mid] 已经在上面比过且不等于 target）；右半有序时用
     nums[mid] < target <= nums[right]，左端是开的。把闭写成开，
     target 恰好等于端点值时会被判到另一半去，返回 -1。
  4. 相等判断必须放在最前面。若先按范围收缩再判等，nums[mid] 恰是答案时
     会被自己的收缩规则排除出区间。
  5. 闭区间写法的三处必须配套：right 初值取 n - 1、循环条件 while left <= right、
     两支各写 mid + 1 与 mid - 1。任缺一处要么漏解要么死循环，
     例如 while left < right 会漏掉区间只剩一个元素的那一轮，
     nums = [1]、target = 1 直接返回 -1。
  6. 找不到返回 -1，不是 None、不是抛异常。判题严格比对返回值。

样例复核：
    nums = [4,5,6,7,0,1,2]、target = 0，区间 [0, 6]：
        mid = 3，nums[3] = 7 不是 0；nums[0] = 4 <= 7，左半 [4,5,6,7] 有序，
            0 不在 [4, 7) 里，往右收：left = 4
        区间 [4, 6]，mid = 5，nums[5] = 1 不是 0；nums[4] = 0 <= 1，
            左半 [0,1] 有序，0 落在 [0, 1) 里，往左收：right = 4
        区间 [4, 4]，mid = 4，nums[4] = 0 命中，返回 4，与样例一致。
    target = 3 时同样走三轮，区间收空，返回 -1；nums = [1]、target = 0 时
    第一轮就 nums[0] != 0，区间收成空，返回 -1。两者都与样例一致。
"""
from typing import List, Optional


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # 闭区间 [left, right]，两端都还没被检查过
        left = 0
        right = len(nums) - 1
        # 闭区间配 <=：left == right 时区间还剩一个元素，那一格仍要查。
        # 写成 < 会漏掉它，长度为 1 的数组直接答错
        while left <= right:
            mid = (left + right) // 2
            # 相等判断必须放最前：否则 mid 恰是答案时会被下面的收缩规则排除出区间
            if nums[mid] == target:
                return mid
            # 断点只有一个，所以 [left, mid] 与 [mid, right] 至少有一段完整有序。
            # 用 <= 而不是 <，是为了照顾 left == mid（区间只剩一两个元素时会出现），
            # 此时左半只有一个元素，算作有序
            if nums[left] <= nums[mid]:
                # 左半 nums[left..mid] 升序，可以直接按值域判断 target 在不在里面。
                # 左端闭右端开：nums[mid] 上面已经比过且不等于 target
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    # 不在有序的左半里，只可能在含断点的右半
                    left = mid + 1
            else:
                # nums[left] > nums[mid] 说明断点落在左半，于是右半 nums[mid..right] 升序。
                # 左端开右端闭，理由与上面对称
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    # 不在有序的右半里，只可能在含断点的左半
                    right = mid - 1
        # 两支都把 mid 踢出了区间，区间每轮至少缩短 1；
        # 因 left > right（区间为空）退出，说明数组里没有 target
        return -1
