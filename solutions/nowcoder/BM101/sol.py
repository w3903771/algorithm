# 来源: 牛客 · 面试必刷TOP101　较难
# 链接: https://www.nowcoder.com/practice/93aacb4a887b46d897b00823f30bfea1
# 判题: 核心代码模式
# 签名: LFU(operators: integer[][]、k: integer) -> integer[]

"""BM101 设计LFU缓存结构 —— 按「使用次数」分桶，每桶内部再按时间排序，淘汰最小桶的队首。

这题考什么：
    LFU（Least Frequently Used，最不经常使用）的淘汰规则是**两级**的：
    先比使用次数，次数相同再比上次使用时间（早的先走）。
    所以光有一条 LRU（最近最少使用）链不够，得让「同频次的记录」自己排成一队。

    结构就是「频次 -> 该频次下的 LRU 队列」：

        freq_map:  freq -> OrderedDict(key -> value)   同频次内，队首最久未用
        key_freq:  key  -> freq                        反查某个 key 现在几次
        min_freq:  当前最小频次，淘汰时直奔这一桶

    一次访问（get 命中或 set 已存在）只做一件事：把 key 从 freq 桶挪到 freq+1 桶，
    进入新桶时挂到队尾（最新）。挪走后如果旧桶空了、且它正好是 min_freq，
    那 min_freq 只可能加一——因为这次访问后该 key 的频次就是 min_freq+1，
    没有别的记录会落在两者之间。这一步是 O(1) 的关键，不用重新扫描求最小值。

    插入新 key 时频次固定为 1，于是 min_freq 直接置 1；
    满员则先从 freq_map[min_freq] 里 popitem(last=False) 淘汰队首。

        k=3   set(1,1) set(2,2) set(3,2) set(2,4) set(3,5)
        freq=1: [1]        freq=2: [2, 3]
        set(4,4) 触发淘汰 -> 取 min_freq=1 桶的队首 -> 淘汰 key 1

数据规模与复杂度：
    0 < k <= 1e5，操作数 n <= 1e5（备注给的是 1 <= k <= n <= 1e5），
    参数满足 |x|,|y| <= 2e9，时限「C/C++ 2 秒，其他语言 4 秒」。
    题面只要求 get 与 set 是 O(log n)，本解法做到 O(1)：
    每次操作至多是常数次字典与有序字典的增删，全程 O(n)、空间 O(k)。
    若淘汰时现扫一遍求最小频次（O(k)），最坏 1e5 * 1e5 = 1e10 次比较，必然超时。

坑在哪：
  1. 本题**不是设计题形式**。签名 LFU(operators, k) 一次性接收整个操作数组，
     由题解自己按 op[0] 分发：1 表示 set(x, y)（op 长度为 3），2 表示 get(x)（长度为 2），
     并且只为每个 get 追加一个返回值。
     同题单里的 BM100（LRU）走的才是设计题约定——判题器构造 Solution(capacity) 后逐个调方法。
     两题外形相近、入口完全相反，照着 BM100 的样子写成类方法，在这里一个测试点都过不了。
  2. min_freq 必须增量维护。它只在两处变动：插入新 key 时置 1；
     touch 把旧桶掏空且旧桶正是 min_freq 时加 1。此外任何操作都不会让最小频次下降，
     所以不需要遍历所有桶去求最小值。
  3. 同频次内部还要再按时间排序——这正是「次数相同时删最早调用的那个」这条规则。
     用普通 dict 存桶在 CPython 里虽然也保序，但没有 O(1) 的「弹出最旧一项」，
     OrderedDict 的 popitem(last=False) 才是对的工具。
  4. set 一个已存在的 key：先记一次使用再写新值。touch 之后该 key 的频次已经变成 f+1，
     所以回写时要用**更新后**的频次去索引桶，用旧频次会写进一个已经不含它的桶里。
  5. 淘汰时三处状态要一起清：桶里的记录、空掉的桶本身、以及 key_freq 里的反查项。
     漏掉 key_freq，被淘汰的 key 之后会被当成命中，返回一个早已不存在的值。
  6. get 未命中返回 -1 是题面规定的约定值，而 value 本身也可能是负数；
     判题按这套约定比对，不必为「-1 究竟是值还是缺失」另做区分。

样例复核：
    k=3，依次 set(1,1)、set(2,2)、set(3,2) 后三者频次都是 1；
    set(2,4) 与 set(3,5) 把 2、3 抬到频次 2，此时最小频次桶里只剩 key 1；
    get(2) 返回 4；set(4,4) 触发淘汰，弹掉最小频次桶的队首 key 1；
    最后 get(1) 返回 -1。输出 [4,-1]，与示例一致。
"""
from collections import OrderedDict, defaultdict
from typing import List, Optional


class Solution:
    def LFU(self, operators: List[List[int]], k: int) -> List[int]:
        # freq_map[f] 是频次为 f 的记录组成的 LRU 队列：队首最久未使用
        freq_map = defaultdict(OrderedDict)
        key_freq = {}          # key -> 当前频次
        min_freq = 0           # 当前存在的最小频次，淘汰时直接查这一桶
        res: List[int] = []

        def touch(key: int) -> int:
            """把 key 的频次 +1，挪到新桶的队尾，返回它的值。"""
            nonlocal min_freq
            # 先从旧桶摘下；旧桶若因此空掉，还要顺手把 min_freq 抬高一格
            f = key_freq[key]
            value = freq_map[f].pop(key)
            if not freq_map[f]:
                del freq_map[f]
                if min_freq == f:
                    min_freq = f + 1     # 旧桶空了，最小频次只可能是它自己 +1
            key_freq[key] = f + 1
            freq_map[f + 1][key] = value
            return value

        # 主循环：op[0] 是操作码，1 为 set(x, y)、2 为 get(x)，只有 get 产出答案
        for op in operators:
            if op[0] == 1:
                key, value = op[1], op[2]
                # 容量为 0 的退化输入：无处安放，这次 set 直接忽略
                if k <= 0:
                    continue
                if key in key_freq:
                    # 已存在：更新值 + 记一次使用，不占新容量
                    touch(key)
                    freq_map[key_freq[key]][key] = value
                    continue
                if len(key_freq) >= k:
                    # 满员：淘汰最小频次桶的队首（同频次里上次使用最早的）
                    old, _ = freq_map[min_freq].popitem(last=False)
                    if not freq_map[min_freq]:
                        del freq_map[min_freq]
                    del key_freq[old]
                # 新 key 落地：频次记 1，值写进 1 号桶的队尾（最新端）
                key_freq[key] = 1
                freq_map[1][key] = value
                min_freq = 1             # 新记录频次为 1，最小频次必然回到 1
            else:
                key = op[1]
                # get：命中则顺带记一次使用，未命中按题面约定记 -1
                res.append(touch(key) if key in key_freq else -1)
        return res
