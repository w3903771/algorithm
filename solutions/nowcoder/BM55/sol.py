# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/4bcf3081067a4d028f95acee3ddcd2b1
# 判题: 核心代码模式
# 签名: permute(num: integer[]) -> list<list<integer>>

"""BM55 没有重复项数字的全排列 —— 先排序再回溯，used 标记已占用的下标，产出即字典序。

这题考什么：
    回溯的标准骨架：**每一层决定排列的第几个位置放谁**。

        dfs():
            len(path) == n   ->  收下一份答案
            否则 for j in 0 .. n-1:
                used[j] 为真就跳过（这个下标已经在 path 里了）
                选：path 追加 num[j]，used[j] 置真
                递归
                撤销：path 弹出末位，used[j] 置假

    「选择 -> 递归 -> 撤销」三步缺一不可，撤销漏掉就会把上一条分支的状态带进下一条。
    深搜与回溯的通用写法见 docs/search/dfs.md。

    每层都从下标 0 扫到 n-1（靠 used 排除已用的），而不是像组合题那样从 start 开始——
    这正是排列与组合的分界：排列关心顺序，同一批数字的不同排列都要算。

数据规模与复杂度：
    0 < n <= 6，时限其他语言 2 秒。
    排列共 n 的阶乘 = 最多 720 份，每份要拷贝长度 n 的列表，时间 O(n 乘 n 的阶乘)，
    递归深度只有 6。这个量级下唯一需要操心的是输出格式，不是性能。
    空间 O(n)：path 与 used 各占一条，答案本身不计。

坑在哪：
  1. 结果必须按**字典序升序**输出（题面「以数字在数组中的位置靠前为优先级，
     按字典序排列输出」），牛客严格比对，顺序错就是错。
     开头的 sorted 不能省：输入若是 [3,1,2]，不排序时第一份产出就是 [3,1,2]，
     整份输出都不在字典序上。
  2. 排好序之后为什么产出恰好是字典序：每层的 for 从小下标扫到大下标，
     取到的值也就从小到大，于是先生成的排列在第一个不同的位置上取值更小，
     这正是字典序的定义。
  3. 收答案时必须写 path[:] 做一份拷贝。path 是全程复用的同一个列表，
     直接追加它本身的话，res 里存的全是同一个对象的引用，
     回溯结束时 path 已被弹空，输出会变成一堆空列表。
  4. 撤销要同时恢复 path 与 used 两处状态，只恢复一处，后面的分支就会读到脏标记。
  5. 交换法（把 num[j] 换到当前位置再递归）同样能枚举全排列，
     但交换会打乱剩余元素的相对顺序，产出不是字典序，还得末尾统一排序才能交题。

样例复核：
    [1,2,3] 的产出顺序：[1,2,3]、[1,3,2]、[2,1,3]、[2,3,1]、[3,1,2]、[3,2,1]，
    与样例给出的顺序逐字一致。
"""
from typing import List, Optional


class Solution:
    def permute(self, num: List[int]) -> List[List[int]]:
        num = sorted(num)               # 升序 + 逐下标枚举 = 输出即字典序
        n = len(num)
        # res 收答案，path 是当前正在拼的排列，used 记录哪些下标已被占用
        res = []
        path = []
        used = [False] * n

        def dfs():
            # 排列填满就收工；path[:] 是必需的拷贝，path 本身还要继续被改
            if len(path) == n:
                res.append(path[:])
                return
            # 每层都从下标 0 扫起（组合题才从 start 扫起），顺序不同的排列都要算
            for j in range(n):
                if used[j]:
                    continue            # 这个下标已经在 path 里了
                used[j] = True          # 选
                path.append(num[j])
                dfs()
                # 撤销要成对：path 与 used 只恢复一处，后面的分支就会读到脏状态
                path.pop()
                used[j] = False

        dfs()
        return res
