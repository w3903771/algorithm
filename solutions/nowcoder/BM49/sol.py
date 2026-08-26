# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/c215ba61c8b1443b996351df929dc4d4
# 判题: 核心代码模式
# 签名: solve(s: string) -> integer

"""BM49 表达式求值 —— 按「表达式 -> 项 -> 因子」三层递归下降解析，用调用栈天然处理优先级与括号。

这题考什么：
    麻烦不在计算而在**解析**：要同时处理多位数、乘法优先于加减、任意层嵌套的括号。
    递归下降是最不容易写错的写法——把文法拆成三层，优先级直接体现在层次里：

        expr   := term (('+' | '-') term)*                最外层，只管加减
        term   := factor ('*' factor)*                    中间层，只管乘法
        factor := 数字 | '(' expr ')' | ('+'|'-') factor    最内层，原子

    因为 term 会把连续的乘法**吃干净**才返回给 expr，乘法自然先于加减完成，
    不需要显式的优先级表；遇到 '(' 就递归回 expr，返回时括号内部已经算成一个数，
    嵌套多少层都由调用栈记着。

    实现上用一个游标 self.i 从左扫到右，三层递归共享它，每个字符只读一次。
    游标只前进不回退，这是复杂度为线性的根据。

数据规模与复杂度：
    0 <= |s| <= 100，保证计算结果始终在整型范围内，时限「其他语言 2 秒」。
    时间 O(n)：跳空格、读数字、吃括号都只让游标前进。
    空间 O(n)：递归深度与括号嵌套层数同阶，|s| <= 100 时最多嵌套 50 层、
    每层三个栈帧，仍远低于 Python 默认的 1000 层递归上限。
    Python 的整数自动扩位，题面「结果在整型范围内」的保证在这里不必额外处理。

坑在哪：
  1. 多位数必须用 while 连着读到非数字为止。一位一位当独立数字处理，
     "12+3" 会被解析成 1、2 两个数，后面的运算全乱。
  2. 一元正负号出现在**因子位置**而不是二元运算位置："-2+3"、"3*(-2)" 都是合法输入。
     只在 expr 层按二元加减处理，遇到开头的 '-' 会取不到左操作数。
     所以 factor 里单独识别前缀 +/-，对后面的因子整体取号。
  3. 加减在循环里就地结算，保证**左结合**：1-2-3 按 (1-2)-3 得 -4；
     若先把右边整段算完再统一相减，会变成 1-(2-3) = 2。
  4. 括号必须在 factor 层处理并递归回 expr：这样括号内部是一个完整的表达式，
     内部的加减也能正确地先于外层的乘法算完，(2*(3-4))*5 才能得到 -10（示例 2）。
  5. 空格可能出现在任何位置，每个决策点前都要先跳一次；只在开头去一次空格，
     "1 + 2" 里的第二个空格仍会把解析卡住。
  6. 读不到数字时返回 0（空串、或多出来的运算符），保证函数总有返回值，
     不会因为返回 None 而在上层做算术时报 TypeError。

样例复核：
    "(2*(3-4))*5"：factor 见到 '('，递归进 expr 解析 "2*(3-4)"；
    其中 term 先取因子 2，遇 '*' 后再取一个因子——又是括号，递归得 3-4 = -1，
    于是 term 返回 -2；回到最外层 term，继续吃 '*' 与因子 5，得 -10，与示例 2 一致。
"""
from typing import List, Optional


class Solution:
    def solve(self, s: str) -> int:
        # 解析入口：游标归零，从最低优先级的 expr 层开始向下递归
        self.s = s
        self.i = 0                      # 全局游标，各层递归共享，保证每个字符只读一次
        return self._expr()

    # 空格可能出现在任何位置，每个决策点前都先跳一次
    def _skip(self) -> None:
        while self.i < len(self.s) and self.s[self.i] == " ":
            self.i += 1

    def _expr(self) -> int:
        """expr := term (('+' | '-') term)*　—— 最低优先级的加减。"""
        val = self._term()
        # 循环里就地结算，保证左结合：1-2-3 按 (1-2)-3 算，而不是 1-(2-3)
        while True:
            self._skip()
            if self.i < len(self.s) and self.s[self.i] in "+-":
                op = self.s[self.i]
                self.i += 1
                right = self._term()    # 右边先把乘法结算干净再回来
                val = val + right if op == "+" else val - right
            else:
                return val              # 碰到 ')' 或串尾就交还给上一层

    def _term(self) -> int:
        """term := factor ('*' factor)*　—— 连续的乘法在这里一次吃完，故优先于加减。"""
        val = self._factor()
        while True:
            self._skip()
            # 只要还连着 '*' 就在本层继续吃，乘法因此总比外层的加减先算完
            if self.i < len(self.s) and self.s[self.i] == "*":
                self.i += 1
                val *= self._factor()
            else:
                return val

    def _factor(self) -> int:
        """factor := 一元正负号 factor | '(' expr ')' | 多位整数。"""
        self._skip()
        # 因子位置上的 +/- 只能是一元符号（如 "-2+3"），对整个后继因子取号
        if self.i < len(self.s) and self.s[self.i] in "+-":
            op = self.s[self.i]         # 记下符号，随后对整个后继因子取号
            self.i += 1
            val = self._factor()
            return val if op == "+" else -val
        # 括号本身也是一个因子：递归回最低优先级层，嵌套深度由调用栈负责
        if self.i < len(self.s) and self.s[self.i] == "(":
            self.i += 1                 # 吃掉 '('
            val = self._expr()          # 返回时括号内部已缩成一个数
            self._skip()
            if self.i < len(self.s) and self.s[self.i] == ")":
                self.i += 1             # 吃掉 ')'
            return val
        start = self.i                  # 数字串的起点，末尾切片时要用
        # 连着读完所有数字字符，否则多位数会被拆成若干个一位数
        while self.i < len(self.s) and self.s[self.i].isdigit():
            self.i += 1
        return int(self.s[start:self.i]) if start != self.i else 0
