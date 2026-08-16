"""BISHI137 【模板】完全背包 —— 每种物品可取无限件，多组数据。

这题考什么：
    完全背包的一维写法：**容量正序遍历**
        for c in range(w, m+1): f[c] = max(f[c], f[c-w] + v)
    正序意味着 f[c-w] 可能已经包含了本物品，于是天然允许取多件。
    （对比 01 背包的倒序——一个字之差，语义完全不同。）

Python 关键（这题是本批最吃常数的一道）：
    正序循环有**串行依赖**，没法直接写成一次 map。解决办法是**倍增（二进制拆分）**：
        依次用 (w, v)、(2w, 2v)、(4w, 4v)... 各做**一次 01 背包**，
        每轮可选可不选，组合起来正好覆盖 0 ~ 2^r-1 件——
        只要 2^r·w > m，就覆盖了所有可能的件数。
    每一轮都是一次 C 层的 `map(max, ...)`，轮数只有 log2(m/w) 层。

    两条必须做的剪枝（否则 T=200 × n=1000 × m=1000 = 2e8，稳挂）：
      1. **按体积去重**：同体积只留价值最大的（体积 <= m，最多 m 种）；
      2. **去支配**：按体积升序扫，只保留价值**严格大于**此前所有更小体积物品的。
         若 w1 <= w2 且 v1 >= v2，物品 2 永远可以被物品 1 替换掉。
    题目的测试点说明里「体积均小于 10」的几个点，去重后只剩 <= 9 件物品，瞬间出解。

数据规模与复杂度：
    T <= 200，n, m <= 1e3。剪枝后单组约 O(Σ_w m·log(m/w)) ≈ 2.4 m^2 次 C 层元素操作。

⚠️ Python 现实性：随机数据（测试点 1-4）下去重后仍可能剩近 1e3 种体积，
    200 组累计约 5e8 次 C 层元素操作，**在 10 秒限制下偏险**；
    体积集中的测试点（5-9）则轻松通过。做法已是 Python 下的最优形态，
    题面本身也建议提交 PyPy。

坑在哪：
  1. 倍增时 (kw, kv) 要同步翻倍，只翻体积不翻价值是常见笔误；
  2. 循环条件是 `kw <= m`，不是 `k <= m//w`（后者会多做一轮无用功）；
  3. 多组数据每组都要重置 dp。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    p = 0
    T = int(data[p]); p += 1
    out = []
    for _ in range(T):
        n = int(data[p]); m = int(data[p + 1])
        p += 2
        best = {}
        for _ in range(n):
            w = int(data[p]); v = int(data[p + 1])
            p += 2
            if w <= m and v > best.get(w, 0):
                best[w] = v                  # 剪枝 1：同体积只留最大价值
        items = []
        mx = 0
        for w in sorted(best):               # 剪枝 2：去掉被更小体积支配的物品
            v = best[w]
            if v > mx:
                items.append((w, v))
                mx = v
        f = [0] * (m + 1)
        for w, v in items:
            kw, kv = w, v
            while kw <= m:                   # 倍增：1 件、2 件、4 件……各做一次 01 背包
                f[kw:] = list(map(max, f[kw:], [x + kv for x in f[:m + 1 - kw]]))
                kw <<= 1
                kv <<= 1
        out.append(f[m])
    sys.stdout.write("\n".join(map(str, out)) + "\n")


main()
