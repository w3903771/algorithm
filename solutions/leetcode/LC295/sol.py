"""LC295 数据流的中位数 —— 用两个堆把数据劈成前后两半，中位数永远在两个堆顶。

这题考什么：
    数据是流式来的，每次 addNum 之后都可能被问中位数。
    维护一个有序列表，插入要 O(n) 的元素搬移；每次现排序是 O(n log n)。
    5e4 次调用下都嫌重，而且都在做「全局有序」这件本题并不需要的事。

    中位数只关心**中间那一两个数**，两侧内部怎么排根本无所谓。
    所以把已有元素劈成两半：

        small —— 较小的那一半，只需要随时取出其中的**最大值**
        large —— 较大的那一半，只需要随时取出其中的**最小值**

    「随时取极值并支持插入」正是堆（优先队列）的定义，
    见 docs/ds/heap.md。两个堆各 O(log n) 插入，
    取中位数则是 O(1) 的读堆顶。

    再约定一条**大小不变量**：len(small) == len(large) 或者恰好多 1。
      两边等长（总数为偶数）-> 中位数 = (small 的最大值 + large 的最小值) / 2
      small 多一个（总数为奇数）-> 中位数 = small 的最大值
    于是 findMedian 永远只看两个堆顶，不需要遍历。

    Python 的 heapq 只有**小顶堆**，没有大顶堆。让 small 表现得像大顶堆的办法是
    **存相反数**：压入 -x、弹出后再取一次相反数。因为 a > b 等价于 -a < -b，
    小顶堆里最小的 -x 对应的正是原值最大的 x。这是 heapq 的标准用法，
    比自定义比较器省事，也不需要包装类。

    插入时的「过一遍手」技巧保证了两半的划分始终正确：
    新元素先无条件进 small，再把 small 的最大值挪给 large，
    最后若 large 变得比 small 长就挪回来一个。
    这样即使新元素本该属于较大的一半，也会被第二步自动送过去，
    不需要写「和堆顶比大小决定进哪个堆」的分支。

数据规模与复杂度：
    -1e5 <= num <= 1e5，addNum 与 findMedian 合计最多 5e4 次调用，
    题面保证 findMedian 之前至少已有一个元素。
    addNum 是 O(log n)（固定三次堆操作），findMedian 是 O(1)，
    空间 O(n)。总时间约 5e4 * log(5e4)，轻松通过。

坑在哪：
  1. 判题按力扣的设计题约定驱动（见 scripts/corerun.py 的 call_design）：
     ops[0] 是**类名** "MedianFinder" 表示构造，args[0] 是构造参数，
     输出数组首位固定为 null。类名必须叫 MedianFinder，__init__ 不接受额外参数。
  2. **small 存的是相反数**，所以取它的最大值要写 -small[0]，
     压入要写 heappush(small, -x)。少取一次相反数，符号就反了，
     中位数会变成一个负得离谱的数。这是本题最容易写漏的一处。
  3. **addNum 里的三步顺序不能改**：先无条件压进 small，
     再把 small 的堆顶转移到 large，最后按需回填。
     若改成「先比大小再决定进哪个堆」，等值元素与边界情况都要额外判断；
     现在这套写法把「元素该归哪一半」交给堆自己解决。
  4. **回填的判断是 len(large) > len(small)，不是 >=**。
     用 >= 会在两边等长时也回填，破坏「small 至多比 large 多一个」的不变量，
     总数为偶数时就取不到正确的两个中间值。
  5. **偶数情况必须做浮点除法**。`(a + b) / 2` 在 Python 3 里已是真除法，
     但写成 `// 2` 会向下取整，[1, 2] 的中位数会算成 1 而不是 1.5。
  6. 题面允许 1e-5 的误差，但这里的结果本来就是精确的：
     两个整数相加再除以 2，只可能是整数或恰好半整数，二进制浮点都能精确表示，
     所以判题即使按严格相等比对也能通过。
  7. 单元素时 small 长度 1、large 长度 0，走的是奇数分支，读 -small[0]；
     large 为空时绝不会去读 large[0]，这由不变量保证。
  8. 严格比对：中位数是一个确定的数值，没有多解。

样例复核：
    操作 addNum(1), addNum(2), findMedian, addNum(3), findMedian。
        addNum(1)  压 small：small = [-1]；转移：large = [1]，small = []；
                   large 比 small 长 -> 回填：small = [-1]，large = []
                   状态：small 的最大值 1，large 空
        addNum(2)  压 small：small = [-2, -1]（堆顶 -2，即最大值 2）；
                   转移堆顶：large = [2]，small = [-1]；两边等长，不回填
                   状态：small = {1}，large = {2}
        findMedian 等长 -> (1 + 2) / 2 = 1.5
        addNum(3)  压 small：small = [-3, -1] -> 转移 3：large = [2, 3]，small = [-1]；
                   large 比 small 长 -> 回填 2：small = [-2, -1]，large = [3]
                   状态：small = {1, 2}，large = {3}
        findMedian small 多一个 -> 返回 small 的最大值 2.0
    输出 [null, null, null, 1.5, null, 2.0]，与题面一致。
    addNum(3) 那一步说明了「先进 small 再转移」的价值：3 明明属于较大的一半，
    却不需要任何比较分支，两次堆操作就自动把它送到了 large。
"""
import heapq
from typing import List, Optional


class MedianFinder:
    def __init__(self):
        # 较小的那一半，需要随时取其中的**最大值**。
        # heapq 只有小顶堆，所以这里**存相反数**：压 -x、读 -small[0]。
        # 因为 a > b 等价于 -a < -b，小顶堆里最小的 -x 正对应原值最大的 x
        self.small = []
        # 较大的那一半，需要随时取其中的最小值，正好是 heapq 的原生行为
        self.large = []

    def addNum(self, num: int) -> None:
        # 第一步：新元素无条件进 small（记得取相反数）。
        # 不先比大小，是为了免掉「该进哪一半」的分支判断
        heapq.heappush(self.small, -num)
        # 第二步：把 small 当前的最大值转移给 large。
        # 弹出的是 -最大值，取相反数还原后再压进 large。
        # 有了这一步，即使新元素本该属于较大的一半，也会被自动送过去
        heapq.heappush(self.large, -heapq.heappop(self.small))
        # 第三步：维持不变量「small 与 large 等长，或 small 恰好多一个」。
        # 判断必须是严格大于——用 >= 会在两边等长时也回填，
        # 打破不变量，偶数个元素时就取不到正确的两个中间值
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def findMedian(self) -> float:
        # small 多一个说明总数为奇数，中位数就是它的最大值（别忘了取相反数）
        if len(self.small) > len(self.large):
            return float(-self.small[0])
        # 两边等长说明总数为偶数，取两个堆顶的平均。
        # 必须用 / 而不是 //：整除会把 [1, 2] 的中位数压成 1
        return (-self.small[0] + self.large[0]) / 2
