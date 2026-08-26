"""LC35 搜索插入位置 —— 找第一个不小于 target 的下标，二分「下界」模板的原型题。

这题考什么：
    题面把两种情形分开说——找到就返回它的下标，找不到就返回它该插进去的位置——
    但这两句话说的是**同一个量**：

        答案 = 满足 nums[k] >= target 的最小下标 k；若不存在这样的 k，答案是 n。

    数组无重复且升序，所以 target 存在时这个最小的 k 就是它自己的位置；
    target 不存在时，k 左边的元素全都 < target、k 及其右边的元素全都 > target，
    把 target 插在下标 k 上，数组仍然升序。一个式子覆盖两种情形，
    代码里因此没有任何「找到了没有」的分支。

    这个量正是标准库 bisect_left 的语义，也是二分四种边界写法里的「下界」
    （写法一：找第一个满足判定的位置），见 docs/basic/binary-search.md 的 44.2 节。
    判定函数取 check(k) = (nums[k] >= target)，数组升序保证它沿下标单调：
    从左到右是 False...False True...True，二分要定位的就是这条分界线。

    本题解手写二分而不是直接调 bisect_left，是因为它是后面 LC34 / LC74 / LC153
    共用的骨架：搜索区间取**左闭右开** [left, right)，循环不变量是

        left 左边的元素已确认全部 < target；
        right 及其右边的位置已确认「满足 check」（right 是当前已知的最小满足位置）。

    答案始终夹在 [left, right) 这段未定区间里，区间空掉时 left 就是那条分界线。

数据规模与复杂度：
    1 <= nums.length <= 1e4，元素与 target 都在 [-1e4, 1e4]，数组升序且无重复。
    时间 O(log n)：每轮区间长度至少减半，n = 1e4 时至多 14 轮。
    空间 O(1)，只用了三个下标变量。
    从左往右线性扫描找第一个 >= target 的位置是 O(n)，本题 n 只有 1e4，
    这样写也能过，但题面明确要求 O(log n)，线性做法不满足要求。

坑在哪：
  1. right 的初值是 n，不是 n - 1。多出来的这一格代表「数组里没有任何元素
     >= target」，此时答案恰好就是 n（插到末尾）。写成 n - 1 就丢掉了这个位置，
     nums = [1,3,5,6]、target = 7 会返回 3 而不是 4。
  2. 循环条件是 left < right。左闭右开区间里 left == right 表示区间为空，
     分界线已经被夹住，必须停下。写成 <= 会去访问 nums[right]，
     right 可以等于 n，当场下标越界。
  3. mid 必须下取整。由 left < right 可推出 left <= mid < right，
     于是 left = mid + 1 让左端严格右移、right = mid 让右端严格左移，
     两支都真正缩短区间。若把 mid 改成上取整，right = mid 这一支在
     right == left + 1 时会写回 right 自己，区间纹丝不动，直接死循环。
  4. 相等的情形（nums[mid] == target）必须走 right = mid 这一支，
     也就是和「大于」归为一类。归到 left = mid + 1 那一支就会跳过 target 本身，
     nums = [1,3,5,6]、target = 5 会返回 3 而不是 2。
  5. 循环退出时返回的是 left 而不是 mid。mid 只是最后一次探测的位置，
     未必是分界线；而 left == right 时不变量恰好说明 left 左边全 < target、
     left 及其右边全 >= target，这正是答案的定义。
  6. 本题走严格比对：答案是唯一的一个整数下标，不存在多解。

样例复核：
    nums = [1,3,5,6]、target = 2，n = 4，区间从 [0, 4) 开始。
        left=0 right=4 -> mid=2，nums[2]=5 >= 2，right=2
        left=0 right=2 -> mid=1，nums[1]=3 >= 2，right=1
        left=0 right=1 -> mid=0，nums[0]=1 <  2，left=1
        left == right == 1，返回 1，与样例一致（2 插在 1 和 3 之间）。
    target = 7 时三轮都走 left = mid + 1 分支，最终 left = 4 = n，与样例一致。
"""
from typing import List, Optional


class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        # 搜索区间取左闭右开 [left, right)。循环不变量：left 左边的元素全部 < target，
        # right 及其右边的位置全部满足 nums[k] >= target，答案夹在这段未定区间里
        left = 0
        # right 初值取 n 而不是 n - 1：多出的这一格代表「全都小于 target」，
        # 此时答案正是 n（插到末尾），于是不必再写特判
        right = len(nums)
        # left == right 时区间为空，分界线已被夹住，必须停下；
        # 写成 <= 会让 right 取到 n，nums[right] 当场越界
        while left < right:
            # 下取整。由 left < right 可得 left <= mid < right，
            # 两个分支于是都能让区间真正缩短，不会死循环
            mid = (left + right) // 2
            if nums[mid] < target:
                # mid 及其左边全部 < target，整段排除；分界线只可能在右半边
                left = mid + 1
            else:
                # nums[mid] >= target，mid 本身就是一个候选答案。右开区间里 right 记的是
                # 「已知的最小满足位置」，所以令 right = mid 是把 mid 登记下来，而不是丢掉它。
                # 相等必须走这一支：归到上面那支会把 target 自己跳过去
                right = mid
        # 退出时 left == right：左边全 < target、自己及右边全 >= target，正是答案的定义。
        # 返回 mid 是错的——mid 只是最后一次探测的位置，未必落在分界线上
        return left
