# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/9be0172896bd43948f8a32fb954e1be1
# 判题: 核心代码模式
# 签名: 需实现 Insert、GetMedian，判题走 driver.py

"""BM48 数据流中的中位数 —— 大顶堆装较小的一半、小顶堆装较大的一半，两个堆顶夹住中位数。

这题考什么：
    每插入一个数就重新排序是 O(n log n)、全程 O(n^2 log n)；
    而求中位数其实只关心「排序后正中间那一两个数」，不必真的全排好。

    把数据流劈成两半，各用一个堆守住交界处：

      - small：**大顶堆**，装较小的一半，堆顶是这半边的最大值；
      - large：**小顶堆**，装较大的一半，堆顶是这半边的最小值。

    不变量有两条：small 里的每个数都不大于 large 里的每个数；
    len(small) == len(large) 或 len(small) == len(large) + 1。
    于是中位数只看两个堆顶：元素个数为奇数时是 small 的堆顶，
    偶数时是两个堆顶的平均值。

    插入的标准写法是「先过一遍对面再收回来」：
    新数先压进 small，把 small 的堆顶弹给 large（保证它确实属于较大的一半），
    若 large 反而更多了，再把 large 的堆顶弹回 small。
    这样无需按大小关系写分支，也不会出现「small 里混进了比 large 更大的数」。

    Python 的 heapq 只有小顶堆，small 靠**存相反数**模拟大顶堆，读取时取负还原。
    堆的性质见 docs/ds/heap.md。

数据规模与复杂度：
    数据流中数的个数 1 <= n <= 1000，1 <= val <= 1000，时限「其他语言 2 秒」。
    Insert 是 O(log n)（每次至多五次堆操作：一压、一弹一压，再平衡时又一弹一压），
    GetMedian 是 O(1)；读满整个数据流是 O(n log n)、空间 O(n)，正好是题面进阶要求的量级。
    「每次插入后重排一遍」在 n = 1000 时约 1e3 * 1e4 次比较，本题其实也过得去，
    但它随 n 平方增长，换成十万级数据流就彻底不可用。

坑在哪：
  1. 调用约定要看清：输入是一串数字，判题**每读入一个就 Insert 一次、紧接着
     GetMedian 一次**，期望输出是各次中位数按 %.2f 格式化、用空格分隔拼成的
     **一个字符串**，末尾还带一个空格（[5,2,3] 对应 "5.00 3.50 3.00 "）。
     这套约定从签名里推不出来，判题走 driver.py。
     若按「读完整个数组再求一次中位数」去理解，全部测试点都会错。
  2. 返回值必须是浮点。偶数个时写成整除，3.5 会变成 3，格式化出来是 "3.00"；
     除数写 2.0（或先转 float）才稳。
  3. small 存的是相反数，取值时必须再取一次负号还原，漏掉符号会得到中位数的相反数。
  4. 「先压 small、再把 small 堆顶弹给 large」这两步不能省。
     直接按大小分支塞进某一边，会出现 small 里混进比 large 堆顶更大的数，
     此时两个堆顶就不再是中位数的边界，答案随数据顺序时对时错。
  5. 不变量选的是「small 可以比 large 多一个」。若允许 large 更多，
     奇数个时读 small 堆顶就读错了；两处（Insert 的再平衡与 GetMedian 的判断）必须同向。

样例复核：
    [5,2,3] 逐个插入：只有 5 时 small = {5}，中位数 5.00；
    插入 2 后 small = {2}、large = {5}，取平均得 3.50；
    插入 3 后 small = {2,3}、large = {5}，奇数个读 small 堆顶 3，得 3.00。
    拼成 "5.00 3.50 3.00 "，与示例 1 的前三项一致。
"""
import heapq
from typing import List, Optional


class Solution:
    def __init__(self) -> None:
        # 不变量：small 的每个数 <= large 的每个数，且 len(small) - len(large) 只能是 0 或 1
        self.small: List[int] = []    # 大顶堆（存相反数）：较小的一半
        self.large: List[int] = []    # 小顶堆：较大的一半

    def Insert(self, num: int) -> None:
        # 先进 small 再吐一个给 large，保证跨堆的大小关系天然成立
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))
        # 只允许 small 比 large 多一个，方便奇数个时直接读 small 堆顶
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def GetMedian(self) -> float:
        # 只读两个堆顶，不做任何堆调整，所以是 O(1)
        if len(self.small) > len(self.large):    # 奇数个：正中间那个在 small 顶上
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2.0   # 偶数个：两个堆顶取平均
