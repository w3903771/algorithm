"""BISHI78 全排列 —— 按字典序输出 1..n 的全部排列，n <= 9。

这题考什么：
    DFS 回溯的入门模板：第 k 层枚举「还没用过的最小可用数字」，
    因为每层都按 1..n 升序尝试，天然就是字典序输出。

数据规模与复杂度：
    n <= 9 -> 9! = 362880 行，每行 9 个数。总输出约 6.5 MB。
    时间复杂度 O(n! * n)，n = 9 时约 3.3e6 次基本操作，本身很快，
    **真正的瓶颈在 IO**。

Python 的选择与坑：
  1. itertools.permutations 对「已排好序的输入」产出的顺序就是字典序，
     它和上面那个 DFS 是同一棵搜索树的同一种遍历次序，只是循环在 C 层跑，
     比手写 Python 递归快一个数量级，所以这里直接用它；
     （递归深度只有 n <= 9 层，本题不存在递归深度问题。）
  2. 绝对不能 for p in ...: print(p)——36 万次 print 会把时间全耗在 IO 上。
     必须先 "\\n".join 拼成一整块再一次 write；
  3. 预先把 1..n 转成 str，join 时就不用反复 map(str, ...)；
  4. 输出格式是每行 n 个整数、单个空格分隔，行内不能有多余空格，
     所以用 " ".join 而不是 print(*p) 之外的拼法；n = 1 时输出就是一行 "1"。
"""
import sys
from itertools import permutations


def main() -> None:
    n = int(sys.stdin.buffer.read().split()[0])
    digits = [str(i) for i in range(1, n + 1)]      # 已升序 -> 排列即字典序
    join = " ".join                                 # 提前绑定，36 万次调用省下属性查找
    # 每个排列拼成一行，再把 9! 行一次性拼成整块写出：全程只有一次 write
    sys.stdout.write("\n".join(map(join, permutations(digits))) + "\n")


main()
