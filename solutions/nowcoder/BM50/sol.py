# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/20ef0972485e41019e39543e8e895b7f
# 判题: 核心代码模式
# 签名: twoSum(numbers: integer[]、target: integer) -> integer[]

"""BM50 两数之和 —— 一遍哈希，边扫边查 target 减当前值是否已经出现过。

这题考什么：
    用哈希表把「找搭档」从一次线性扫描降成一次 O(1) 查询，是空间换时间的最小样板。

        seen = {}                       值 -> 它在数组里的下标
        遍历到 numbers[i] = x：
            need = target - x
            need 在 seen 里  ->  seen[need] 与 i 就是答案
            否则              ->  记下 seen[x] = i，留给后面的数来配

    **先查后存**是这份写法的关键：查询时表里只有下标严格小于 i 的元素，
    x 自己还没进表。由此得到两个附带保证——不会把同一个元素用两次，
    以及 seen[need] < i，返回的两个下标天然升序。
    哈希表的性质见 docs/ds/hash.md。

数据规模与复杂度：
    2 <= len(numbers) <= 1e5，元素与 target 都在 1e9 量级，时限其他语言 2 秒。
    一遍扫描 O(n)，字典占 O(n) 空间，优于题面要求的 O(n log n)。
    两重循环枚举数对是 1e5 的平方除以二 = 5e9 次，Python 每秒千万级操作，必然超时。
    排序加双指针也是 O(n log n)，但排序会打乱原下标，还得额外保存「值到原位置」的
    映射，反而比哈希表麻烦。

坑在哪：
  1. 返回的下标**从 1 开始**（题面原文「返回的数组下标从 1 开始算起」）。
     逻辑全对却忘了加一是这题最常见的丢分点，示例 1 的 [3,2,4] 与 target = 6
     期望输出 [2,3] 而不是 [1,2]，正好能暴露。
  2. 顺序不能颠倒成「先存后查」。target 恰为某个元素两倍时，
     先存会让它自己查到自己，返回两个相同的下标。
  3. 同值元素在表里只保留最后一次出现的下标。题目保证有解，被覆盖后仍能配出
     一组合法答案，所以不必存下标列表。
  4. 末尾的空列表只是兜底。题目保证 target 一定可由两个数相加得到，
     循环里必然 return；删掉它则无解时函数隐式返回 None，判题会报类型错误。

样例复核：
    numbers = [3, 2, 4]，target = 6。
        i=0  x=3  need=3  表空            ->  seen = {3: 0}
        i=1  x=2  need=4  没有            ->  seen = {3: 0, 2: 1}
        i=2  x=4  need=2  命中 seen[2]=1  ->  返回 [1+1, 2+1] = [2, 3]
    与样例一致。若此处漏了加一，输出会是 [1, 2]。
"""
from typing import List, Optional


class Solution:
    def twoSum(self, numbers: List[int], target: int) -> List[int]:
        # 值 -> 下标；只存已经扫过的元素，是「先查后存」的前提
        seen = {}                       # 下标先按 0-based 记
        for i, x in enumerate(numbers):
            need = target - x
            # 先查后存：表里只有 i 之前的元素，既不会自己配自己，配对下标也天然升序
            if need in seen:
                return [seen[need] + 1, i + 1]  # 题面要求下标从 1 开始
            seen[x] = i                 # 当前元素留给后面的数来配
        return []                       # 题目保证有解，正常走不到这里
