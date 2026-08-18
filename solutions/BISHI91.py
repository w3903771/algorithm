"""BISHI91 拼接木棍 —— n 根小木棍拼回若干根等长大木棍，求原始长度的最小可能值。

这题考什么：
    经典的「木棒 / Sticks」搜索题（POJ 1011），核心是 **DFS + 一大堆剪枝**，
    没有剪枝的裸搜索是纯指数级，必然超时。
    搜索与剪枝的通用手法见 docs/part5-搜索/62-记忆化搜索与剪枝.md。

    枚举原始长度 L（必须满足 max(a) <= L <= sum(a) 且 L | sum(a)），
    然后 DFS 判断能否把所有木棍恰好分成 sum/L 组、每组和为 L。
    第一个可行的 L 就是答案（从小到大枚举）。

    五个关键剪枝（缺一个都可能 TLE）：
      1. 木棍**降序**排序：先放长的，搜索树上层的分支数更少，失败得更早；
      2. 同一组内选取的下标必须递增（避免同一组合被换序重复搜索）；
      3. **若当前组是空的（还没放任何棍），放入最长的可用棍却最终失败，
         则整个 L 无解**——因为这根棍总要落在某个组里，
         而各组是等价的，换个组也一样失败；
      4. **若某根棍恰好把当前组填满（rest == len）却失败，则整个 L 无解**——
         恰好填满是这根棍能做的最好情况，它都不行就没救了；
      5. 相同长度的木棍在同一位置失败后，跳过后面所有等长的棍。

数据规模与复杂度：
    n <= 60，每根 <= 50 -> sum <= 3000。约数个数不多，
    配上上述剪枝，搜索规模在毫秒级。
    递归深度最多 n = 60 层，**远低于 CPython 默认的 1000 层上限，
    所以本题保留递归写法，不需要改迭代**。

坑在哪：
  1. L 必须整除 sum，且 L >= max(a)（最长的那根不能被切开）；
  2. used 数组要在回溯时正确还原；
  3. 剪枝 3 和 4 是「直接返回 False」而不是「continue」，写错就退化成暴力；
  4. 从小到大枚举 L，第一个成功的即答案；L = sum 一定成功（就一根），
     所以循环不会落空。

样例复核：
    9 根 [5,2,1,5,2,1,5,2,1]，sum = 24，max = 5。
    L = 6 可行：(5,1) (5,1) (5,1) (2,2,2)，输出 6 ✓
    （L = 4 虽然整除 24，但小于 max = 5，最长的一根就放不下，因此不在枚举范围内。）
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    a = sorted((int(v) for v in data[1:1 + n]), reverse=True)   # 剪枝1：降序
    total = sum(a)
    used = [False] * n                                          # 该棍是否已归入某一组

    def dfs(groups_left: int, rest: int, start: int) -> bool:
        """还要拼 groups_left 组，当前组还差 rest，从下标 start 起挑棍。"""
        if groups_left == 0:
            return True
        if rest == 0:                                  # 当前组拼满，开下一组
            return dfs(groups_left - 1, L, 0)
        prev = -1                                      # 上一根「试过并失败」的棍长
        for i in range(start, n):
            if used[i] or a[i] > rest:                 # 已用掉，或塞不进当前组的余量
                continue
            if a[i] == prev:                           # 剪枝5：跳过等长的失败分支
                continue
            used[i] = True
            if dfs(groups_left, rest - a[i], i + 1):   # 剪枝2：下标递增
                return True
            used[i] = False
            prev = a[i]
            # 剪枝3：当前组还空着，最长可用棍都失败 -> 该 L 无解
            if rest == L:
                return False
            # 剪枝4：这根棍恰好填满当前组却失败 -> 该 L 无解
            if a[i] == rest:
                return False
        return False

    # 从小到大枚举原始长度，第一个可行的 L 即答案
    for L in range(a[0], total + 1):               # 下界是最长的一根，它不能被切开
        if total % L:                              # 不整除就分不成若干等长的组
            continue
        for i in range(n):
            used[i] = False                        # 换一个 L 重搜，标记全部还原
        if dfs(total // L, L, 0):
            sys.stdout.write("%d\n" % L)
            return


main()
