"""LC17 电话号码的字母组合 —— 每个数字贡献一层选择，逐位往下选，选满就收一份答案。

这题考什么：
    这是回溯的最基本形态：**多个独立选择维度的笛卡尔积**。
    第 i 层对应 digits 的第 i 位，这一层的候选就是该数字键上的 3 到 4 个字母；
    层与层之间互不牵制，选完最后一位就得到一份组合。

        digits = "23"
                  root
              a /  b|  c            第 0 层：数字 2 的 abc
             /     |     ...
          d e f  d e f              第 1 层：数字 3 的 def
          ->  ad ae af be bf ... cf

    「选择 -> 递归 -> 撤销」三步：把字母压进 path、递归到下一位、弹出复原。
    撤销漏掉的话，path 会越堆越长，第二条分支就会带着上一条的残留继续拼。
    深搜与回溯的通用写法见 docs/search/dfs.md。

    这题的选择之间没有互斥关系（同一个字母可以在不同位重复出现），
    所以既不需要 used 标记，也不需要 start 下标，纯粹是逐层展开。

数据规模与复杂度：
    1 <= digits.length <= 4，每个数字最多映射 4 个字母（7 和 9 是 pqrs、wxyz）。
    答案条数最多 4 的 4 次方 = 256 条，每条长 4，
    时间 O(4 的 n 次方 乘 n)，实际不到两千次基本操作，怎么写都够快。
    空间 O(n)：path 与递归栈都只有 4 层深，答案本身不计入。

坑在哪：
  1. 数字到字母的映射必须逐键核对：2=abc、3=def、4=ghi、5=jkl、6=mno、
     7=**pqrs**（四个字母）、8=tuv、9=**wxyz**（四个字母）。
     把 7 和 9 也当成三个字母，是这题最常见的错法，样例的 "23" 完全测不出来。
  2. 题面写 digits.length >= 1，但**边界描述不是担保**：力扣的实际数据里存在
     digits = "" 的用例，期望输出是空列表 []。不特判的话，dfs(0) 会立刻命中
     「选满了」的出口，往结果里塞进一个空串，返回 [""] 而不是 []。
  3. 收答案时必须写 "".join(path) 生成一个新字符串。path 是全程复用的同一个列表，
     直接把 path 本身追加进 res，回溯结束时它已被弹空，输出会变成一堆空列表。
  4. 本题在 meta.json 的 judge 里配了 unordered：题面明写「答案可以按任意顺序返回」，
     因为组合之间没有先后语义，谁先谁后都是同一个解集。
     放宽的只是**顶层顺序**——每个组合本身是一个有序字符串，"ad" 与 "da" 不是一回事，
     字母的先后必须严格跟着 digits 的位序。顺序放宽也不等于内容放宽：
     多吐一条重复组合照样判错。本题各层选的是不同位，天然不会重复，无须额外去重。

样例复核：
    digits = "23"：第 0 层依次取 a、b、c，每取一个字母后第 1 层再依次取 d、e、f，
    产出 ["ad","ae","af","bd","be","bf","cd","ce","cf"]，
    共 3 乘 3 = 9 条，与样例一致。
"""
from typing import List, Optional


class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        # 力扣实际数据里有 digits = "" 的用例，期望 []；不特判会返回 [""]
        if not digits:
            return []
        # 电话键盘映射，注意 7 是 pqrs、9 是 wxyz，各有四个字母
        mapping = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl",
                   "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
        # res 收答案，path 是当前正在拼的那条组合（按位存字母）
        res = []
        path = []

        def dfs(i: int) -> None:
            # 每一位都定好了就收一份；join 生成新串，path 本身还要继续被改
            if i == len(digits):
                res.append("".join(path))
                return
            # 第 i 层的候选 = digits 第 i 位那个键上的全部字母
            for ch in mapping[digits[i]]:
                path.append(ch)     # 选：把这个字母定在第 i 位
                dfs(i + 1)          # 递归：去决定第 i+1 位
                path.pop()          # 撤销：弹回来，让第 i 位换下一个字母

        dfs(0)
        return res
