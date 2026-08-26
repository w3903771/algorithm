"""LC153 寻找旋转排序数组中的最小值 —— 拿 nums[mid] 和右端点比，大就说明断点在右边。

这题考什么：
    旋转后的数组是**两段各自升序**的拼接，且左段的每个数都大于右段的每个数
    （元素互不相同，所以是严格大于）。要找的最小值就是第二段的开头，即旋转点：

        [4,5,6,7 | 0,1,2]
                   ^ 答案

    数组整体无序，但「mid 落在哪一段」这个局部判断就足以排除一半区间。
    判断的比较对象必须选**右端点** nums[right]：

        nums[mid] > nums[right]
            左段的每个数都大于右段的每个数，而 nums[right] 一定在右段
            （或者整段有序时它就是全局最大），所以 mid 只能在左段。
            最小值严格在 mid 右侧  ->  left = mid + 1，把 mid 一并排除

        nums[mid] < nums[right]
            mid 落在右段（或整段本来就有序），mid 自己就可能是最小值，
            不能丢  ->  right = mid

    元素互不相同，相等的情形不会发生，两支就分完了全部情况。
    这是二分四种写法里的写法一（下界，mid 下取整、循环条件 left < right），
    见 docs/basic/binary-search.md 的 44.2 节。收敛到 left == right 时，
    那一格就是答案。

    整段有序（题面所说的旋转 n 次，如 [11,13,15,17]）不需要特判：
    此时每一轮都有 nums[mid] < nums[right]，right 一路左移到 0，返回 nums[0]，
    正是最小值。

    换个角度看，这就是在**布尔序列上求下界**：把「nums[k] <= nums[n-1]」当判定，
    沿下标它恰好是 False...False True...True，第一个 True 就是旋转点。
    代码里比的是 nums[right] 而不是固定的 nums[n-1]，两者等价——
    right 始终落在右段一侧，比较结果相同，但省掉一个变量。

数据规模与复杂度：
    1 <= n <= 5000，元素在 [-5000, 5000] 且**互不相同**，
    题面保证数组是升序数组旋转 1 到 n 次的结果（旋转 n 次即原数组）。
    时间 O(log n)：n = 5000 时至多 13 轮。空间 O(1)。
    直接 min(nums) 是 O(n)，5000 的规模跑得动，但题面明确要求 O(log n)。

坑在哪：
  1. 必须和**右端点**比，不能和左端点比。nums[mid] > nums[left] 时，
     mid 可能在左段（[4,5,6,7,0,1,2] 里 mid 指向 6），也可能在整段有序的数组里
     （[11,13,15,17] 里 mid 指向 15），两种情形要往相反方向收，
     单凭这一个比较分不出来，还得额外拿 nums[left] 与 nums[right] 比一次。
     和右端点比就没有这个歧义。
  2. 两支的收缩幅度不对称：left = mid + 1 把 mid 排除掉（已确认它在左段，
     不可能是最小值），right = mid 保留 mid（它可能就是答案）。
     把后者写成 right = mid - 1 会漏掉答案本身；把前者写成 left = mid
     则在区间只剩两个元素时原地打转，死循环。
  3. 循环条件是 left < right，不是 <=。left == right 时区间只剩一格，
     它就是答案，必须停下。改成 <= 会让 mid == left == right，
     此时 nums[mid] > nums[right] 是「自己大于自己」，恒不成立，
     于是走 right = mid 把 right 赋回它自己，区间纹丝不动——**死循环**。
     实测 [3,4,5,1,2] 与 [11,13,15,17] 都会卡在这里转不出来。
  4. mid 取下取整。由 left < right 可得 left <= mid < right，
     于是 right = mid 一定让右端严格左移。若改成上取整，
     right == left + 1 时 mid == right，right = mid 原地不动，死循环。
  5. 返回的是**最小值本身**，不是它的下标。题面问的是元素值。
  6. 「互不相同」是本题只需两个分支的前提。对照牛客 BM21 旋转数组的最小数字：
     那题是非降序数组旋转，**允许重复**，会出现 nums[mid] == nums[right]
     （比如 [1,0,1,1,1]）而判不出断点在哪一侧的局面，只能保守地
     right -= 1 退一格，最坏退化成 O(n)。本题不会遇到这一支。

样例复核：
    nums = [3,4,5,1,2]，区间 [0, 4]：
        mid = 2，nums[2] = 5 > nums[4] = 2，mid 在左段，left = 3
        区间 [3, 4]，mid = 3，nums[3] = 1 < nums[4] = 2，right = 3
        left == right == 3，返回 nums[3] = 1，与样例一致。
    nums = [11,13,15,17]（整段有序）：
        mid = 1，13 < 17，right = 1；mid = 0，11 < 13，right = 0，
        返回 nums[0] = 11，与样例一致，无需特判。
"""
from typing import List, Optional


class Solution:
    def findMin(self, nums: List[int]) -> int:
        # 闭区间 [left, right]，答案（旋转点）始终落在里面
        left = 0
        right = len(nums) - 1
        # left == right 时区间只剩一格，它就是答案，必须停下；写成 <= 会让
        # mid == left == right，nums[mid] > nums[right] 恒不成立，right = mid 原地不动，死循环
        while left < right:
            # 下取整，保证 left <= mid < right，于是 right = mid 一定让右端严格左移，
            # 不会原地打转。上取整在此处会死循环
            mid = (left + right) // 2
            # 和**右端点**比：左段的每个数都大于右段的每个数，所以 nums[mid] 更大
            # 就说明 mid 落在左段，最小值严格在它右边，mid 可以一并排除。
            # 换成和左端点比会分不清「整段有序」与「mid 在左段」两种情形
            if nums[mid] > nums[right]:
                left = mid + 1
            else:
                # nums[mid] < nums[right]：mid 落在右段（或整段本来就有序），
                # 它自己就可能是最小值，只能收到 mid，不能写 mid - 1。
                # 元素互不相同，相等的情形不会出现，两支已覆盖全部情况
                right = mid
        # 收敛到单点，这一格就是旋转点。题目要的是元素值而不是下标
        return nums[left]
