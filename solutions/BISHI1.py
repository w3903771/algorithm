"""BISHI1 【模板】序列操作 —— 动态数组的 8 种操作（尾插/尾删/下标查/中间插/升序/降序/求长/打印）。

这题考什么：
    最基础的「变长数组 = Python list」模板题。8 个操作全都能直接映射到
    list 的原生方法上，重点是读清楚每个操作的语义。

数据规模与复杂度：
    q <= 7e3，规模很小，可以放心用 O(q) 次 O(n) 的操作：
      - 操作 4 的中间插入 list.insert 是 O(n)，最坏 7e3 * 7e3 ≈ 5e7 次
        元素搬移，但底层是 C 的 memmove，实测毫秒级；
      - 操作 5/6 的整体排序单次 O(n log n)，最坏 7e3 次排序也只有 ~1e8，
        而且 Timsort 对「已经有序 / 完全逆序」的数组是 O(n)（会直接识别
        出单调 run），连续的 5 5 5 或 5 6 5 6 都退化不了。
    所以不需要平衡树 / 块状链表，直接 list 就是本题的正解。

坑在哪：
    1. 操作 4 是「在下标 i 与 i+1 之间插入」，也就是 insert(i + 1, x)，
       不是 insert(i, x)，差一位就全错；
    2. 下标从 0 开始；
    3. 操作 8 要把整个序列打印成一行、空格分隔，用 " ".join 而不是
       循环 print，否则 IO 会被打爆；
    4. 操作 2/5/6/7/8 这几行只有一个数字，不能无脑按「每行两个数」读，
       按 token 游标逐个取才不会错位。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    q = int(data[0])
    i = 1
    a = []
    out = []
    for _ in range(q):
        op = data[i]
        i += 1
        if op == b"1":                       # 尾部追加
            a.append(int(data[i]))
            i += 1
        elif op == b"2":                     # 删除尾部（保证非空）
            a.pop()
        elif op == b"3":                     # 查下标
            out.append(str(a[int(data[i])]))
            i += 1
        elif op == b"4":                     # 在 i 与 i+1 之间插入 -> insert(i+1)
            p = int(data[i])
            a.insert(p + 1, int(data[i + 1]))
            i += 2
        elif op == b"5":                     # 升序
            a.sort()
        elif op == b"6":                     # 降序
            a.sort(reverse=True)
        elif op == b"7":                     # 长度
            out.append(str(len(a)))
        else:                                # op == b"8"，整个序列
            out.append(" ".join(map(str, a)))
    sys.stdout.write("\n".join(out) + "\n")


main()
