"""BISHI90 【模板】记忆化搜索 —— 给定分段递归式 f(a,b,c)，多组询问 f(a,b,c) mod 1e9+7。

这题考什么：
    记忆化搜索 / 递推。递归式是：
        a<=0 或 b<=0 或 c<=0            -> 1
        a < b 且 b < c                   -> f(a,b,c-1) + f(a,b-1,c-1) - f(a,b-1,c)
        其它                              -> f(a-1,b,c) + f(a-1,b-1,c)
                                            + f(a-1,b,c-1) - f(a-1,b-1,c-1)
    朴素递归是指数级（每次分裂成 3~4 个子问题、深度上百），必须记忆化。
    由于 1 <= a,b,c <= 100，状态总数只有 101^3 ≈ 1.03e6，
    干脆**离线一次性把整张表递推出来**，之后每次询问 O(1) 查表。

    递推顺序：所有转移的下标都不增（且至少有一维严格减小），
    按 a 升序 -> b 升序 -> c 升序扫描时，用到的
      f(a-1, *, *)：上一层 a，已算完；
      f(a, b-1, *)：同层前一个 b，已算完；
      f(a, b, c-1)：同行前一个 c，已算完。
    所以一遍三重循环就够，不需要真的递归（也就绕开了递归深度问题）。
    记忆化与递推的关系见 docs/part5-搜索/62-记忆化搜索与剪枝.md。

数据规模与复杂度：
    表大小 101^3 ≈ 1.03e6，T <= 1e3 次询问 O(1)。

Python 的坑（本题必看）：
  1. 1e6 次 Python 层循环 + 取模在 2 秒限制下相当吃紧。这里做了两处优化：
     - 「其它情况」分支（a >= b，或者 c <= b）的转移**只依赖上一层 a-1**，
       各个 c 之间互不依赖，于是可以用 zip + 列表推导整行批量算出来，
       把内层循环压到 C 层；
     - 只有「a < b 且 c > b」这一段才有 c 方向的串行依赖，必须逐个算，
       但它只占一行的尾部。
  2. 取模不要每一项都取，攒完一个表达式再 % MOD 一次即可（Python 大整数
     不会溢出，少一次取模就快一点）；
  3. 减法后可能为负，最后统一 % MOD 会自动转正（Python 的 % 结果非负）；
  4. lru_cache + 递归写法在 100^3 状态下既慢又会撞递归深度（深度可达 300），
     所以这里选**自底向上递推**，完全不用递归。

样例复核：
    f(1,1,1)：a<b 不成立 -> 分支三 = f(0,1,1)+f(0,0,1)+f(0,1,0)-f(0,0,0)
             = 1+1+1-1 = 2 ✓
    f(2,2,2) = f(1,2,2)+f(1,1,2)+f(1,2,1)-f(1,1,1) = 2+2+2-2 = 4 ✓
"""
import sys

MOD = 10 ** 9 + 7
N = 100


def build():
    """F[a][b] 是一个长度 N+1 的列表，F[a][b][c] = f(a,b,c) mod MOD。"""
    ones = [1] * (N + 1)
    # a = 0 层：base case 全为 1
    F = [[ones] * (N + 1)]               # 同一个 ones 被引用 N+1 次，全程只读故不必复制
    for a in range(1, N + 1):
        pa = F[a - 1]                    # 上一层，分支三的四个转移全落在这里
        layer = [ones]                       # b = 0 -> 全 1
        for b in range(1, N + 1):
            pb = pa[b]                       # f(a-1, b, *)
            pbm = pa[b - 1]                  # f(a-1, b-1, *)
            # 分支三覆盖的 c 范围：a >= b 时是全部；a < b 时是 c <= b
            lim = N if a >= b else b
            # 批量算 c = 1..lim：只依赖上一层 a-1，各 c 互不依赖
            row = [1]                        # c = 0 -> base case
            row.extend([(x + y + u - v) % MOD for x, y, u, v in
                        zip(pb[1:lim + 1], pbm[1:lim + 1], pb[0:lim], pbm[0:lim])])
            if lim < N:
                # a < b 且 c > b：分支二，c 方向串行依赖，逐个算
                cur = layer[b - 1]           # f(a, b-1, *)
                prev = row[lim]              # 从分支三算好的 c = lim 处接着往右推
                for c in range(lim + 1, N + 1):
                    # 分支二：f(a,b,c) = f(a,b,c-1) + f(a,b-1,c-1) - f(a,b-1,c)
                    # prev 正是 f(a,b,c-1)，一次取模即可（Python 大整数不溢出）
                    prev = (prev + cur[c - 1] - cur[c]) % MOD
                    row.append(prev)
            layer.append(row)
        F.append(layer)
    return F


def main() -> None:
    F = build()                          # 离线把整张表推完，之后每次询问只是查表
    data = sys.stdin.buffer.read().split()
    t = int(data[0])
    out = []
    p = 1
    for _ in range(t):
        a = int(data[p]); b = int(data[p + 1]); c = int(data[p + 2]); p += 3
        out.append(str(F[a][b][c]))      # 题面保证 1 <= a,b,c <= 100，下标必在表内
    sys.stdout.write("\n".join(out) + "\n")


main()
