"""BISHI2 【模板】栈的操作 —— push / pop / query / size，空栈时输出 Empty。

这题考什么：
    栈的模板。Python 的 list 就是天然的栈：append 入栈、pop 出栈、
    a[-1] 取栈顶，全是均摊 O(1)。

数据规模与复杂度：
    n <= 1e5，总复杂度 O(n)。规模不大，但操作是「一行一条」的文本，
    仍然用 sys.stdin.buffer.read().split() 一次性读入 + 游标解析，
    避免 1e5 次 input() 的系统调用开销；输出同样攒进 list 最后一次
    write，避免 1e5 次 print。

坑在哪：
    1. pop 在空栈时要输出 Empty（不是静默忽略），非空时**不输出任何东西**，
       只是删除——这一条最容易写反；
    2. query 在空栈时也输出 Empty；
    3. size 永远有输出，空栈时输出 0；
    4. 只有 push 后面跟一个参数，其余三种操作是单 token，必须用游标读。
"""
import sys


def main() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    i = 1
    st = []
    out = []
    for _ in range(n):
        op = data[i]
        i += 1
        if op == b"push":
            st.append(data[i])               # 直接存原始 bytes，省掉 int/str 往返
            i += 1
        elif op == b"pop":
            if st:
                st.pop()                     # 非空时删除，且不输出
            else:
                out.append("Empty")
        elif op == b"query":
            out.append(st[-1].decode() if st else "Empty")
        else:                                # size
            out.append(str(len(st)))
    sys.stdout.write("\n".join(out) + "\n")


main()
