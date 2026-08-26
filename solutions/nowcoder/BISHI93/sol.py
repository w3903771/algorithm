"""BISHI93 【模板】Trie 字典树 —— n 个模式串，q 次询问「有多少模式串以 t 为前缀」。

这题考什么：
    Trie（字典树，把公共前缀合并成一条路径的多叉树，见
    docs/string/trie.md）模板。插入每个模式串时，把它经过的**每一个节点**的
    计数 +1；查询时沿 t 走下去，走得通就输出终点节点的计数，
    走不通输出 0。因为「以 t 为前缀的串」恰好就是「插入时经过了 t 对应节点的串」。

数据规模与复杂度：
    n, q <= 1e5，所有串总长 <= 1e6，字符集是大小写字母（52 种，**区分大小写**）。
    插入 + 查询都是 O(总长)，共约 2e6 次转移。

Python 的实现选择（本题最关键的部分）：
  1. **不要用「把每个前缀切出来当 dict 的 key」**这种偷懒写法。
     总长虽然只有 1e6，但可能是**一个**长度 1e6 的串，
     切出它的全部前缀就是 5e11 次字符拷贝，直接爆炸；
  2. 也不要用「每个节点一个 dict」的 list-of-dict：最多 1e6 个节点，
     1e6 个空 dict 光对象头就上百 MB；
  3. 这里用**单个扁平 dict**：key = node_id * 128 + 字符字节值，value = 子节点 id。
     只有一个 dict、至多 1e6 个 entry，内存和常数都最优，
     而且整数 key 的哈希是恒等映射，查得飞快；
  4. IO 用 sys.stdin.buffer.read().split()：所有串都不含空格，
     按 token 切正好一行一个。

坑在哪：
  1. **区分大小写**（样例里 "Way" 答案是 0 就是在测这个），
     所以不能 lower()，直接用原始字节值当转移字符；
  2. 查询串可能比任何模式串都长，中途没有子节点就要立刻输出 0 并 break；
  3. cnt[节点] 统计的是「经过该节点的插入次数」，根节点（空前缀）不会被查到，
     无需特殊处理。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n, q = int(data[0]), int(data[1])

    child = {}                 # key = node * 128 + byte  ->  子节点编号
    cnt = [0]                  # cnt[v] = 经过节点 v 的模式串数量；0 号是根
    get = child.get

    # ---- 插入 n 个模式串：沿途每个节点的计数 +1 ----
    p = 2
    for _ in range(n):
        s = data[p]; p += 1
        cur = 0                # 每个串都从根节点 0 出发
        for b in s:
            k = cur * 128 + b  # 把 (节点号, 字符) 打包成一个整数当 key
            nxt = get(k, -1)
            if nxt < 0:        # 这条转移还不存在，新建一个节点
                nxt = len(cnt) # 新节点编号 = 当前节点总数
                cnt.append(0)
                child[k] = nxt
            cur = nxt
            cnt[cur] += 1      # 该前缀又多了一个模式串经过

    # ---- q 次查询：沿 t 一路走下去，走得通就读终点节点的计数 ----
    out = []
    for _ in range(q):
        s = data[p]; p += 1
        cur = 0
        for b in s:
            cur = get(cur * 128 + b, -1)
            if cur < 0:        # 中途断路，说明没有模式串以 t 为前缀
                break
        out.append("0" if cur < 0 else str(cnt[cur]))
    sys.stdout.write("\n".join(out) + "\n")


main()
