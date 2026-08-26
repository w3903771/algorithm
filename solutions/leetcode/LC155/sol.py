"""LC155 最小栈 —— 每压一个元素就同时记下「到这一层为止的最小值」，取最小值变成读栈顶。

这题考什么：
    普通栈的四个操作里，push / pop / top 天然都是 O(1)，
    唯独 getMin 麻烦：临时扫一遍栈是 O(n)，题面要求常数时间。

    只用一个变量记最小值行不行？不行。假设 self.min 记着当前最小值 -3，
    pop 把 -3 弹掉之后，新的最小值是多少？这个信息已经丢了，
    只能重新扫描整个栈。**栈的历史状态必须被保留**，因为 pop 会回到历史状态。

    正确做法是让最小值也「跟着栈的层次走」：再开一个等高的辅助栈 mins，
    mins[i] 的含义是**主栈前 i + 1 个元素的最小值**。

        push(x) -> mins 压入 min(x, 当前 mins 栈顶)
        pop()   -> 两个栈同步弹出
        getMin  -> 直接返回 mins[-1]

    循环不变量：两个栈始终等高，且 mins[i] == min(data[0..i])。
    pop 之后 mins 的新栈顶自动就是剩余元素的最小值——历史被完整保留下来，
    不需要任何重算。四个操作全是 O(1)。

    另一种同样常见的写法是让辅助栈只在「新元素小于等于当前最小值」时才压，
    pop 时只在「弹出的元素等于辅助栈顶」时才弹。那样更省空间，
    但相等元素的处理稍不注意就会出错（必须用小于等于，不能用严格小于，
    否则重复的最小值只记一次，第一次 pop 就把它丢了）。
    这里取等高写法：不变量最直白，也不存在相等元素的陷阱。
    栈的基础用法见 docs/ds/stack.md。

数据规模与复杂度：
    -2^31 <= 元素值 <= 2^31 - 1，四种操作合计最多调用 3e4 次。
    每个操作 O(1)，总时间 O(操作数)；空间 O(栈内元素数)，
    因为多存了一份等高的最小值栈，常数是普通栈的两倍——用空间换时间。

坑在哪：
  1. 判题按力扣的设计题约定驱动（见 scripts/corerun.py 的 call_design）：
     ops[0] 是**类名** "MinStack" 表示构造，args[0] 是构造参数，
     输出数组首位固定为 null 对应这次构造。类名必须叫 MinStack，
     且 __init__ 不接受额外参数——改名或加参数会让驱动直接抛错。
  2. **push 的参数名是 value 而不是 val**，签名来自站点官方模板，不能改。
     核心代码模式下驱动是按位置传参的，改名不至于当场出错，
     但仓库的规矩是签名一律照抄模板。
  3. **push / pop / top 都返回 None 或元素值，不要画蛇添足**。
     push 与 pop 在期望输出里就是 null，返回 self 之类的东西会被严格比对判错。
  4. **不能只用一个变量存最小值**。pop 掉当前最小值之后无从恢复上一个最小值，
     只能 O(n) 重扫，题面的常数时间要求就废了。样例里
     push(-2), push(0), push(-3) 之后 pop 掉 -3，getMin 必须变回 -2，
     正是为了考这一点。
  5. **两个栈必须同步增减**。push 时漏压 mins、或 pop 时只弹主栈，
     等高不变量一破，后续 getMin 全部错位，而且错得很晚才暴露。
  6. **min 要和当前 mins 栈顶比，不是和刚 push 的前一个元素比**。
     data 的前一个元素未必是历史最小值；比错对象会让最小值随数据起伏，
     [3, 1, 2] 这样的序列压完就会把最小值记成 2。
  7. 题面保证 pop / top / getMin 只在非空栈上调用，所以不必写空栈保护；
     但也别反过来依赖「空栈时返回某个默认值」，那种情况不会出现。
  8. 严格比对：每次调用的返回值唯一，没有多解。

样例复核：
    操作 push(-2), push(0), push(-3), getMin, pop, top, getMin。
        push(-2)  data = [-2]          mins = [-2]
        push(0)   data = [-2, 0]       mins = [-2, -2]   min(0, -2) = -2
        push(-3)  data = [-2, 0, -3]   mins = [-2, -2, -3]
        getMin    读 mins[-1] = -3
        pop       data = [-2, 0]       mins = [-2, -2]   两栈同步弹出
        top       读 data[-1] = 0
        getMin    读 mins[-1] = -2     历史最小值自动恢复，无需重扫
    输出 [null, null, null, null, -3, null, 0, -2]，与题面一致。
"""
from typing import List, Optional


class MinStack:
    def __init__(self):
        # 主栈：正常存元素
        self.data = []
        # 辅助栈：与主栈**等高**，mins[i] 恒等于 data[0..i] 的最小值。
        # 只用一个变量记最小值是不够的——pop 掉最小值后无法恢复上一个最小值
        self.mins = []

    def push(self, value: int) -> None:
        self.data.append(value)
        # 新的前缀最小值 = 新元素与「原前缀最小值」（即 mins 栈顶）取小。
        # 比较对象必须是 mins 栈顶而不是 data 的前一个元素——
        # 前一个元素未必是历史最小值
        if self.mins:
            self.mins.append(value if value < self.mins[-1] else self.mins[-1])
        else:
            # 栈原本为空，这一个元素自己就是最小值
            self.mins.append(value)

    def pop(self) -> None:
        # 两个栈必须同步弹出，等高不变量一旦破坏，后续 getMin 会全部错位。
        # 题面保证只在非空栈上调用，不需要空栈保护
        self.data.pop()
        self.mins.pop()

    def top(self) -> int:
        return self.data[-1]

    def getMin(self) -> int:
        # 栈顶即当前全部元素的最小值，O(1)，不必扫描
        return self.mins[-1]
