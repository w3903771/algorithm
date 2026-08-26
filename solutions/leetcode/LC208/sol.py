"""LC208 实现 Trie (前缀树) —— 用一棵按字符分叉的多叉树存下所有单词，公共前缀只存一份。

这题考什么：
    Trie（读作 try，中文叫前缀树或字典树）是一棵多叉树：**边**代表一个字符，
    从根走到某个结点所经过的边依次拼起来，就是这个结点代表的那段前缀。
    插入 "apple" 与 "app" 后的形状（每条边上标着字符）：

        root -a-> . -p-> . -p-> [end] -l-> . -e-> [end]

    "app" 与 "apple" 共用前三条边，公共前缀天然只存一份，这正是前缀树省空间的来源。

    三个操作都退化成「从根沿着字符往下走」：
      insert     沿路缺哪条边就补哪条边，走到末尾把该结点标成「单词结尾」。
      search     沿路走，中途断了返回 false；走到末尾还要求该结点是单词结尾。
      startsWith 沿路走，只要没断就返回 true，末尾是不是单词结尾无所谓。

    search 与 startsWith 的唯一差别就是最后那一下要不要看结尾标记——
    没有这个标记就分不清「app 是一个已插入的单词」和「app 只是 apple 的前缀」。

    结点用字典 {字符: 子结点} 而不是长度 26 的定长数组：题面只保证小写字母，
    定长数组也对，但字典按需分配，稀疏的树上省下大把空指针。

    前缀树的完整讲法与更多用法见 docs/string/trie.md。

数据规模与复杂度：
    单串长度 <= 2000，insert / search / startsWith 调用总数 <= 3e4。
    每次操作沿树走的步数等于串长 L，每步是一次字典查找 O(1)，单次操作 O(L)。
    最坏总时间 3e4 * 2000 = 6e7 次字典操作，Python 下偏重但仍在时限内；
    实际数据的串长远达不到上限。空间是所有插入串的字符总数，同样 O(总长)。
    朴素做法「把单词存进 set，startsWith 时遍历整个 set 逐个比前缀」，
    单次前缀查询就要 O(单词数 * L)，3e4 次调用直接退化成平方级。

坑在哪：
  1. 判题按力扣的设计题约定驱动（见 scripts/corerun.py 的 call_design）：
     ops[0] 是**类名** "Trie" 表示构造，args[0] 是构造参数，
     输出数组首位固定为 null 对应这次构造。所以类名必须叫 Trie，
     且 __init__ 不接收额外参数——改名或加参数都会让驱动直接抛错。
  2. insert 与 search 都返回 None（题面签名是 void / boolean），
     insert 那几次调用在期望输出里就是 null。不要画蛇添足返回 self 之类的东西，
     严格比对会把它判成不等于 null。
  3. 「单词结尾」标记不能省，也不能用「该结点没有子结点」来代替。
     插入 "apple" 后 "app" 对应的结点有子结点却不是单词，search("app") 必须为 false；
     反过来同时插入 "app" 与 "apple" 后，"app" 的结点既有子结点又是单词。
     两种性质互相独立，必须各存各的。
  4. search 与 startsWith 只在最后一步不同，共用一个「走到底」的私有辅助函数
     可以避免两处逻辑写岔；若分别复制一遍下行循环，改动时极易只改一处。
  5. 空前缀在本题不会出现（题面保证长度 >= 1），但沿树走的循环天然处理它：
     一步都不走，停在根上，startsWith("") 返回 true，符合「任何串都以空串为前缀」。

样例复核：
    insert("apple") 后 search("apple") 走到末尾且有结尾标记 -> true；
    search("app") 能走通但该结点没有结尾标记 -> false；
    startsWith("app") 不看标记 -> true；
    再 insert("app") 只是给已存在的结点补上结尾标记，search("app") 变成 true。
    输出 [null, null, true, false, true, null, true]，与样例一致。
"""
from typing import List, Optional


class Trie:
    def __init__(self):
        # 根结点不代表任何字符，只是所有单词共同的出发点。
        # children 形如 {字符: 子结点}，用字典而非定长 26 数组，稀疏时省空间
        self.children = {}
        # 标记「有一个单词恰好在这里结束」，与「有没有子结点」是两件独立的事
        self.is_word = False

    def insert(self, word: str) -> None:
        # 从根出发逐字符下行，缺哪条边就现建哪条
        node = self
        for ch in word:
            if ch not in node.children:
                node.children[ch] = Trie()
            node = node.children[ch]
        # 走到末尾才打结尾标记；只建边不打标记的话，search 永远返回 false
        node.is_word = True

    def _walk(self, s: str):
        """沿 s 逐字符下行，走通返回终点结点，中途断链返回 None。"""
        # search 与 startsWith 的下行过程完全相同，抽出来避免两处逻辑写岔
        node = self
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        # 走通还不够：必须是单词结尾。少了后半句，"app" 会因是 "apple" 的前缀而误判为已插入
        return node is not None and node.is_word

    def startsWith(self, prefix: str) -> bool:
        # 前缀查询只关心路径通不通，终点是不是单词结尾无所谓
        return self._walk(prefix) is not None
