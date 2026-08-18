"""BISHI146 收集金币 —— 网格里只能右/下走，格子会在指定回合变墙，求最多金币。

这题考什么：
    先做一步**时间与位置的解耦**，把「动态变墙」化成「静态可达性」：

      小 K 只能右/下走，所以他**第 r 回合结束时必然站在 i+j-2 = r 的那条反对角线上**。
      也就是说，格子 (i, j) 只会在第 r = i+j-2 回合被访问（起点 r = 0）。
      而 (x, y) 从第 v 回合起变墙（回合开始时变化、之后才移动），于是
          (i, j) 可用  <=>  v(i, j) > i + j - 2
      **时间维直接消失了**，剩下的就是最朴素的「网格路径最大权和」DP。
      （题面「起点在第一回合变墙视作不受影响」正好符合这个式子：起点 r = 0 < 1 <= v。）

        f[i][j] = a[i][j] + max(f[i-1][j], f[i][j-1])，不可用的格子记为「不可达」
    答案 = **所有可达格子里 f 的最大值**（他可以随时被堵住而停下，不必走到右下角）。

数据规模与复杂度：
    n, m <= 1000（1e6 个格子），t <= n·m。O(nm) 时间与空间。

坑在哪：
  1. **答案不是 f[n][m]**，而是全局最大值——样例 2 的答案就是只站在起点的 1；
  2. 判定条件的等号：v > i+j-2（严格大于），写成 >= 会多用一个已经变墙的格子；
  3. 「不可达」要和「金币数 0」区分开（a_ij >= 1，所以用 -1 当不可达哨兵是安全的）；
  4. 读入 1e6 个整数 + 1e6 次 DP 迭代，时限「其他语言 2 秒」——
     必须一次性 read().split()，DP 用局部变量缓存行引用，才有希望；
     只有 t 个格子有变墙信息，其余格子永不变墙，用一个 bytearray 标记即可。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); m = int(data[1])
    # 先跳过金币矩阵读变墙信息：t 条信息在矩阵之后，而 DP 需要先知道哪些格子不能用
    p = 2 + n * m
    t = int(data[p]); p += 1
    bad = bytearray(n * m)                   # 1 = 该格在被访问的那一回合已经是墙
    for _ in range(t):
        x = int(data[p]); y = int(data[p + 1]); v = int(data[p + 2])
        p += 3
        if v <= x + y - 2:                   # 到达时刻 r = x+y-2，v <= r 即已变墙
            bad[(x - 1) * m + y - 1] = 1     # 二维坐标压成一维下标，省一层列表嵌套

    p = 2                                    # 游标回到金币矩阵，开始逐行 DP
    NEG = -1                                 # 不可达哨兵（金币数 >= 1，不会撞车）
    prev = [NEG] * m                         # 上一行的 f
    ans = 0
    for i in range(n):
        row = data[p:p + m]                  # 先不转 int，用到哪个转哪个
        p += m
        base = i * m                         # 本行在 bad 里的起始下标
        cur = [NEG] * m
        run = NEG                            # = cur[j-1]，用局部变量代替下标回读
        for j in range(m):
            if bad[base + j]:                # 走到这格时它已是墙，整格作废
                run = NEG                    # 左邻断了，右边的格子不能再从这里接
                continue
            up = prev[j]
            best = up if up > run else run   # 只能从上方或左方来
            if best < 0:                     # 上、左都不可达
                if i or j:                   # 只有起点可以「无前驱」
                    run = NEG
                    continue
                best = 0                     # 起点自己就是路径的开头，前缀收益 0
            v = int(row[j]) + best
            cur[j] = v
            run = v
            if v > ans:                      # 随时可能被堵死，答案取全局最大而非右下角
                ans = v
        prev = cur                           # 只滚动一行，1e6 个格子不必全存
    sys.stdout.write("%d\n" % ans)


main()
