"""BISHI1 【模板】序列操作 —— 动态数组的 8 种操作（尾插/尾删/下标查/中间插/升序/降序/求长/打印）。

这题考什么：
    最基础的「变长数组 = Python list」模板题。8 个操作全都能直接映射到
    list 的原生方法上，重点是读清楚每个操作的语义。
    对照表如下，把题面的每一条翻译成一行代码，这题就没有别的内容了：

        1 x    -> a.append(x)          尾部追加
        2      -> a.pop()              删掉尾部
        3 i    -> a[i]                 按下标取值
        4 i x  -> a.insert(i + 1, x)   在 i 与 i+1 之间插入
        5 / 6  -> a.sort() / a.sort(reverse=True)
        7      -> len(a)
        8      -> " ".join(map(str, a))

    list 的底层是一段连续的指针数组，所以按下标取值是 O(1)、尾部增删是
    均摊 O(1)、中间插入是 O(n)。见 docs/part3-数据结构/30-序列与数组.md。

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
       按 token 游标逐个取才不会错位；
    5. 判断操作类型时比较的是 bytes（b"1" 而不是 "1"），因为
       read().split() 切出来的 token 是 bytes。与 str 比较永远为假，
       会一路落到 else 分支。

样例复核：
    示例 2 的 4 1 4：序列 {5,3,7} 执行 insert(2, 4) 得到 {5,3,4,7}，
    与题面说明一致；若误写成 insert(1, 4) 会得到 {5,4,3,7}，正是坑 1 说的情况。
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
