"""BISHI102 【模板】并查集 —— 支持合并、同集合查询、集合大小查询。

这题考什么：
    并查集（Union-Find）模板，两个优化必须同时上：
      - **路径压缩**：find 时把沿途所有点直接挂到根上；
      - **按大小合并**：把小树挂到大树下，保证树高不会失控。
    两者一起用时单次操作的均摊复杂度是反阿克曼函数 O(α(n))，实际上就是常数。

数据规模与复杂度：
    n, q <= 5e5。总复杂度约 O((n + q) α(n))，但 Python 的常数很重，
    所以下面的写法在细节上做了不少压榨。

Python 的坑（本题必看）：
  1. **路径压缩必须写成迭代版**。递归版 find 在退化链上深度可达 5e5，
     RecursionError 跑不掉；这里用「先找根，再第二遍把沿途节点指向根」
     的两趟迭代写法，无递归、无额外内存；
  2. `size` 数组只在**根**上有意义，合并时把小的加到大的上面；
  3. IO 是本题的另一半瓶颈：5e5 行操作必须一次 read().split() 读完、
     输出 "\n".join 一次 write；
  4. 把 parent / size 绑成局部变量、find 定义在 main 内部（局部作用域查找更快）。

坑在哪：
  1. op = 3 只有一个参数，op = 1/2 有两个，**必须按 token 游标读**，
     不能假定每行固定列数；
  2. 合并时如果 i、j 已经同根要直接跳过，否则 size 会被重复累加；
  3. 输出的是大写 "YES" / "NO"。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0]); q = int(data[1])
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x: int) -> int:
        """迭代式路径压缩：先找到根，再把沿途所有点直接挂到根上。"""
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r

    out = []
    p = 2
    for _ in range(q):
        op = data[p]
        if op == b"3":
            out.append(str(size[find(int(data[p + 1]))]))
            p += 2
            continue
        ra = find(int(data[p + 1]))
        rb = find(int(data[p + 2]))
        p += 3
        if op == b"1":
            if ra != rb:                      # 已同集合则忽略，避免 size 重复累加
                if size[ra] < size[rb]:       # 按大小合并：小挂大
                    ra, rb = rb, ra
                parent[rb] = ra
                size[ra] += size[rb]
        else:                                 # op == b"2"
            out.append("YES" if ra == rb else "NO")
    sys.stdout.write("\n".join(out) + "\n")


main()
