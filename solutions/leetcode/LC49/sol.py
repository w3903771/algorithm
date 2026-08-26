"""LC49 字母异位词分组 —— 给每个词算一个「与字母顺序无关」的指纹，按指纹归堆。

这题考什么：
    字母异位词（anagram，把一个词的字母重新排列得到的另一个词）之间是等价关系：
    自反、对称、传递。要把等价类分出来，只需给每个等价类取一个**规范代表**
    （canonical form，同一类里所有元素都算得出同一个值、不同类必然不同），
    然后拿它当哈希表的键，一遍扫描就能把同类的词收进同一个桶。
    见 docs/ds/hash.md。

    两个词互为异位词，等价于它们的**字母多重集合**相同。多重集合有两种现成的
    规范表示，本题解取第一种：

        1. 把字母排序后拼回字符串："eat" "tea" "ate" 都变成 "aet"
        2. 数 26 个字母各出现几次，做成长度 26 的元组

    排序键实现最短，且排序把 100 个字符排一遍只有 100 * log(100) 次比较，
    比构造并哈希一个 26 元组还便宜。计数键的优势在词很长时（O(L) 对 O(L log L)），
    本题 L <= 100，两者都远不是瓶颈。

    逐对判断「这两个词是不是异位词」是 O(n^2) 次比较，n = 1e4 时 1e8 次，
    而且还得维护「已经分好的组」，写起来更麻烦——归约成查表才是正解。

数据规模与复杂度：
    1 <= len(strs) <= 1e4，0 <= len(strs[i]) <= 100，只含小写字母。
    设 n 为词数、L 为词的最大长度：建键 O(n L log L)，
    最坏 1e4 * 100 * 7 约等于 7e6 次比较，Python 下不到一秒。
    空间 O(n L)——每个词的键与词本身各存一份。

坑在哪：
  1. 键必须用**不可变**类型。`sorted(s)` 返回的是 list，list 不可哈希，
     直接拿它当字典键会 TypeError；要么像这里 `"".join(...)` 拼成字符串，
     要么 `tuple(sorted(s))`。
  2. 空字符串是合法输入（题面示例 2 就是 `strs = [""]`，期望 `[[""]]`）。
     排序后的键是空串 ""，它和别的键一样正常参与分组，不需要特判——
     但如果实现里写了「跳过空串」之类的防御，反而会漏掉这一组。
  3. 判题按 `unordered_deep` 比对，因为题面原文「可以按任意顺序返回结果列表」，
     且组内成员的先后也由实现的扫描顺序决定，没有规定。所以外层组的顺序、
     内层词的顺序都放宽。**顺序放宽不等于内容放宽**：分组的划分必须完全一致，
     多吐一个重复的词、或把一个词漏进两组，照样判错。
  4. 返回的是 `list(groups.values())` 而不是 `groups` 本身。字典的值视图
     （dict_values）不是列表，判题按结构比对时拿到的类型对不上。

样例复核：
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]。
        "eat" -> 键 "aet"   groups = {"aet": ["eat"]}
        "tea" -> 键 "aet"   groups = {"aet": ["eat", "tea"]}
        "tan" -> 键 "ant"   新桶
        "ate" -> 键 "aet"   groups["aet"] = ["eat", "tea", "ate"]
        "nat" -> 键 "ant"   groups["ant"] = ["tan", "nat"]
        "bat" -> 键 "abt"   新桶
    得到 [["eat","tea","ate"], ["tan","nat"], ["bat"]]，
    与题面期望 [["bat"],["nat","tan"],["ate","eat","tea"]] 是同一个划分，
    只差顺序，正是 unordered_deep 放宽的部分。
"""
from typing import List, Optional


class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        # 规范键 -> 该等价类里的所有词。键相同当且仅当两词互为字母异位词
        groups = {}
        for word in strs:
            # 把字母排序再拼回字符串，抹掉原有顺序：这就是多重集合的规范表示。
            # 必须 join 成字符串（不可变、可哈希），sorted 返回的 list 不能当键
            key = "".join(sorted(word))
            # setdefault 让「新键建桶」与「老键追加」合成一步，
            # 空字符串的键就是空串 ""，走的是同一条路径，不需要特判
            groups.setdefault(key, []).append(word)
        # 只要各组的内容，不要键；转成 list 是因为 dict_values 不是列表类型
        return list(groups.values())
