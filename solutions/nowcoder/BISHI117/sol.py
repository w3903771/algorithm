"""BISHI117 小苯的IDE括号问题（easy）—— 光标两侧的删除操作模拟。

这题考什么：
    「光标」型编辑器模拟的标准套路：**用两个栈夹住光标**。
      - 左栈 L 存光标左边的字符，栈顶就是光标左侧第一个字符；
      - 右栈 R 存光标右边的字符，但**逆序存放**，
        这样「光标右侧第一个字符」也在栈顶，pop 是 O(1)。
    两种操作就都变成了 O(1)：
      - backspace：若 L 顶是 '(' 且 R 顶是 ')'，两个一起 pop（成对删除）；
                   否则 L 非空就 pop 一个；
      - delete：R 非空就 pop 一个。
    最终答案 = "".join(L) + "I" + "".join(reversed(R))。

    这就是「链表/双栈实现光标」的经典模型：任何「在中间插入/删除」的题，
    只要修改点是随光标移动的，都可以用双栈把 O(n) 的搬移降到 O(1)。

数据规模与复杂度：
    n, k <= 2e5，总复杂度 O(n + k)。
    如果直接用字符串拼接模拟（每次 s = s[:i] + s[i+1:]），
    单次就是 O(n)，总量 4e10 字符搬移，必然 TLE。

坑在哪：
  1. backspace 的**成对删除优先级最高**：必须先判「左 '(' 且右 ')'」，
     判完再退化成「删左边一个」，顺序反了就错；
  2. 成对删除时右侧那个 ')' 也要删掉，只删左边是最常见的 WA；
  3. 光标左侧为空时 backspace 无效果（不能去 pop 空栈）；
  4. 输出必须带上光标字符 'I'（样例 2 的答案就是单独一个 I）。
"""
import sys


def main() -> None:
    # 每个操作名都是一个不含空格的单词，所以 split() 后
    # data 的布局是：n, k, s, 然后 k 个操作名。n 用不上，直接跳过。
    data = sys.stdin.buffer.read().split()
    k = int(data[1])
    s = data[2].decode()
    i = s.index("I")                         # 'I' 保证恰好出现一次，以它为界劈成两半
    left = list(s[:i])                       # 光标左侧，栈顶 = 最靠近光标的字符
    right = list(s[i + 1:])
    right.reverse()                          # 逆序存放，栈顶 = 光标右侧第一个字符
    for j in range(3, 3 + k):
        if data[j] == b"backspace":
            # 成对删除的优先级最高：先判这一条，判不中才退化成删左边一个
            if left and left[-1] == "(" and right and right[-1] == ")":
                left.pop()                   # 成对删除：一次删掉 () 两个字符
                right.pop()
            elif left:
                left.pop()                   # 左侧为空时 backspace 无效，什么也不做
        else:                                # delete
            if right:
                right.pop()                  # 删的是光标右侧第一个字符，即右栈栈顶
    right.reverse()                          # 反转回正序，才是原文里从左到右的顺序
    sys.stdout.write("".join(left) + "I" + "".join(right) + "\n")   # 光标本身要保留


main()
