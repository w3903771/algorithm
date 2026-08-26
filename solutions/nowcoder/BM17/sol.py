# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/d3df40bd23594118b57554129cadf47b
# 判题: 核心代码模式
# 签名: search(nums: integer[]、target: integer) -> integer

"""BM17 二分查找-I —— 升序无重复数组里定位 target 的下标，不存在则返回 -1。

这题考什么：
    二分查找的最小形态，也是后面 BM18 到 BM21 全部变形的模板来源。
    能二分的唯一理由是「只看中点就能判断 target 在哪半边」：数组升序，
    nums[mid] < target 就意味着 mid 及其左边所有元素都小于 target，
    整个左半段可以一次性排除。每比较一次候选区间减半。

    区间用左闭右闭 [left, right] 表示「尚未排除的下标」，初值 [0, n-1]：

        nums[mid] == target   ->  下标就是 mid，直接返回
        nums[mid] <  target   ->  target 只可能在右半，left = mid + 1
        nums[mid] >  target   ->  target 只可能在左半，right = mid - 1

    左闭右闭与左闭右开 [left, right) 是两套写法，循环条件与边界更新必须成套用，
    混用就会漏解或死循环。两套模板的对照见 docs/basic/binary-search.md。

数据规模与复杂度：
    题面正文给的是 0 <= len(nums) <= 2e5，备注又写「数组元素长度在 [0,10000] 之间」，
    两处不一致，按大的 2e5 算。时限其他语言 2 秒。
    二分 O(log n)，2e5 只需约 18 次比较，空间 O(1)。
    单次查询用线性扫 O(n) = 2e5 其实也不会超时，但题面进阶明确要求 O(log n)；
    真正的分水岭出现在多次查询上——q 次线性扫是 q * 2e5，二分是 q * 18。

坑在哪：
  1. 循环条件必须是 left <= right。右端是闭的，left == right 时区间里还剩一个
     元素没查过；写成 left < right 会把它漏掉，nums = [1]、target = 1 就返回 -1。
  2. 边界更新必须是 mid 加一或减一，不能写成 left = mid。区间长度为 2 时
     mid 恒等于 left，若 left = mid 则区间不再收缩，程序卡死到判题超时。
  3. 空数组不需要特判。len(nums) == 0 时 right = -1，left <= right 一开始就不成立，
     直接落到末尾的 return -1；题面示例 2 给的正是空数组。
  4. mid = (left + right) // 2 在 Python 里可以放心写，因为整数没有位宽上限。
     C/Java 里 left + right 可能超出 int 上限变成负数，导致下标越界，
     那些语言得写成 left + (right - left) // 2。

样例复核：
    nums = [-1,0,3,4,6,10,13,14]，target = 13。
        [0,7]  mid=3  nums[3]=4  < 13  ->  left=4
        [4,7]  mid=5  nums[5]=10 < 13  ->  left=6
        [6,7]  mid=6  nums[6]=13 == 13 ->  返回 6
    与样例输出 6 一致。
"""
from typing import List, Optional


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # 候选区间取左闭右闭：left 与 right 指向的下标都还没被排除
        left, right = 0, len(nums) - 1  # 空数组时 right = -1
        while left <= right:            # 闭区间，剩一个元素也要查
            # Python 整数无上限，相加不会溢出；C/Java 需改写成 left + (right - left) // 2
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            # 两个分支都把 mid 排除在新区间外：它已经比过，留着会让区间停止收缩
            if nums[mid] < target:
                left = mid + 1          # target 在右半
            else:
                right = mid - 1         # target 在左半
        return -1                       # 区间空了（left > right），数组里没有 target
