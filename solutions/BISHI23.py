"""BISHI23 小红书推荐系统 —— 统计出现次数 >= 3 的单词，按频次降序、同频字典序升序输出。

考点：哈希计数 + 多关键字排序。串长 <= 1e5，单词数 O(1e5)，
      Counter 计数 O(L)，排序 O(k log k)，总复杂度 O(L + k log k)。

坑：
  1. 输入是**一整行含空格的字符串**，但因为我们只需要按空格切词，
     直接 read().split() 就够了（split 会顺带吃掉多余空格和换行）。
  2. 排序键是 (-次数, 单词)：先按频次从高到低，频次相同再按字典序升序。
     不能先按字典序排再按次数排（Python 的 sort 稳定，但一次给全 key 更清晰）。
  3. 判定是「不少于 3 次」即 >= 3，不是 > 3。
"""
import sys
from collections import Counter

cnt = Counter(sys.stdin.buffer.read().split())
res = sorted(((-c, w) for w, c in cnt.items() if c >= 3))
sys.stdout.write("".join(w.decode() + "\n" for _, w in res))
