# 来源: 牛客 · 面试必刷TOP101　较难
# 链接: https://www.nowcoder.com/practice/5dfded165916435d9defb053c63f1e84
# 判题: 核心代码模式
# 签名: 设计题，实现 class Solution，方法 get、set

"""BM100 设计LRU缓存结构 —— 哈希表配双向链表，用 OrderedDict 一步到位地维护「访问新鲜度」。

这题考什么：
    LRU（Least Recently Used，最近最少使用）要同时做到两件事，单一结构都办不到：

        按 key 随机存取         -> 哈希表 O(1)，但没有顺序
        按「最久未使用」淘汰    -> 有序序列，但数组头部删除是 O(n)

    经典解法是**哈希表 + 双向链表**：链表按访问时间串起所有记录，
    表头是最新、表尾是最旧；哈希表存 key -> 链表结点，
    于是「找到某结点」O(1)，「把它摘下来挪到表头」也 O(1)——
    双向链表才能在已知结点的情况下 O(1) 摘除，单向链表还得先找前驱。

        set(1,1) set(2,2)   新 [2]<->[1] 旧
        get(1)              1 被访问 -> 挪到表头  新 [1]<->[2] 旧
        set(3,3)  容量 2    淘汰表尾的 2         新 [3]<->[1] 旧

    Python 的 collections.OrderedDict 内部就是这套哈希表加双向链表，
    自己再手搓一遍结点类没有额外收益：

        move_to_end(key)        把已有 key 挪到「最新」一端
        popitem(last=False)     弹出最旧的一条，即 LRU 淘汰

    两个方法都是 O(1)，正好对上题面「set 和 get 必须以 O(1) 的方式运行」。

数据规模与复杂度：
    1 <= capacity <= 1e5，操作次数 1 <= n <= 1e5，0 <= key,val <= 2e9，
    时限「C/C++ 2 秒，其他语言 4 秒」。get 与 set 都是 O(1)，全程 O(n)、空间 O(capacity)。
    若改用一个 list 记访问顺序，每次刷新新鲜度都要 O(capacity) 地搬移元素，
    1e5 * 1e5 = 1e10 次操作，必然超时——这题的「O(1) 要求」不是形式主义。

坑在哪：
  1. 这题走的是设计题的调用约定：牛客喂进来的是「操作名数组, 参数数组, 构造参数」，
     形如 ["set","set","get",...], [[1,1],[2,2],[1],...], 2；
     判题器先用构造参数 Solution(2) 建对象，再按操作序列逐个调用同名方法，
     把每个 get 的返回值收集成答案数组（set 的返回位由系统填 "null"，题解不用管）。
     题解只需实现 __init__ / get / set，**不要**自己去解析那个操作数组。
     同题单里的 BM101（LFU）恰恰相反，是一次性把操作数组传给函数，两者别搞混。
  2. get 命中后也要刷新新鲜度。题面提示 1 写明「某个 key 的 set 或 get 操作一旦发生，
     则认为这个 key 的记录成了最常使用的」；漏掉这一步，示例里 get(1) 之后
     被淘汰的会是 1 而不是 2，从第 5 个输出起全错。
  3. set 一个已存在的 key 是「更新值 + 刷新新鲜度」，容量没有变化，不该触发淘汰。
     而且直接赋值**不会**改变 OrderedDict 里的既有顺序，必须补一次 move_to_end。
  4. 淘汰用 popitem(last=False) 取最旧的一端；默认的 popitem() 弹的是最新端，正好反了，
     变成「谁刚用就淘汰谁」。
  5. 淘汰的判断是「插入之后长度超过 capacity」，先插再淘汰与先淘汰再插等价，
     但不能写成「长度等于 capacity 就淘汰」——那会在容量还没用满时误删。

样例复核：
    capacity=2，依次 set(1,1)、set(2,2) 后新鲜度是 [2, 1]；
    get(1) 返回 1 并把 1 刷新到最新端，得 [1, 2]；
    set(3,3) 超容，淘汰最旧的 2，得 [3, 1]；此后 get(2) 返回 -1，与题面示例一致。
"""
from collections import OrderedDict
from typing import List, Optional


class Solution:
    def __init__(self, capacity: int):
        # 容量在构造时定死，之后每插入一个新 key 都要与它比对
        self.capacity = capacity
        # 有序字典的迭代顺序即访问顺序：队首最久未使用，队尾最新
        self.cache: "OrderedDict[int, int]" = OrderedDict()

    def get(self, key: int) -> int:
        # 未命中按题面约定返回 -1，且不改动任何记录的新鲜度
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)      # 命中也算一次使用，刷新到最新端
        return self.cache[key]

    def set(self, key: int, value: int) -> None:
        if key in self.cache:
            # 已存在的 key：只更新值并刷新新鲜度，容量不变，因此不进入下面的淘汰分支
            self.cache[key] = value
            # 直接赋值不会改动既有顺序，必须显式挪到最新端
            self.cache.move_to_end(key)
            return
        self.cache[key] = value              # 新 key 直接落在最新端
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)   # 超容才淘汰队首，即最久未使用的那条
