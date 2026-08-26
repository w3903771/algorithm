"""LC146 LRU 缓存 —— 设计一个定容缓存，get 与 put 都要 O(1)，容量满时淘汰最久未使用的键。

这题考什么：
    LRU（Least Recently Used，最近最少使用）要求同时具备两种能力：

      - 按 key 瞬间找到值            -> 哈希表（Python 的 dict）
      - 按「最近使用时间」瞬间排出先后 -> 有序结构，且能 O(1) 地把任意元素挪到最前

    单靠 dict 排不出使用顺序；单靠列表/数组虽然有序，但把中间某个元素挪到队首要搬动
    后面所有元素，是 O(n)。答案是**两者组合**：哈希表 + 双向链表。

      - 双向链表按「最近使用」从头到尾排列：头部最新、尾部最旧；
      - 哈希表存 key -> 该 key 在链表里的**节点对象**。

    有了节点对象的直接引用，摘除只需改左右邻居的两个指针，不用从头找起，
    这正是双向链表相对单向链表的价值（单向链表拿不到前驱，摘除要 O(n) 找）。
    于是 get 与 put 都退化成「查表 + 摘除 + 插到表头」这三个常数时间动作。

    链表与哈希表的基础见 docs/ds/linked-list.md 与
    docs/ds/hash.md。

    头尾各放一个**哨兵**节点，真实节点永远夹在两者之间。这样摘除与插入
    都不必判断「是不是第一个/最后一个」，代码里没有任何 None 判断。

数据规模与复杂度：
    容量 1..3000，key 取 0..10000，value 取 0..10^5，get 与 put 合计最多 2 * 10^5 次。
    每次操作都是常数次字典查询与指针赋值，O(1) 时间；空间 O(capacity)。
    总工作量约 2 * 10^5 次常数操作，Python 下毫无压力。

    把「最近使用」用一个自增时间戳记在字典里、淘汰时线性扫出最小时间戳的写法，
    单次淘汰是 O(capacity)，最坏 2 * 10^5 * 3000 = 6 * 10^8 次比较，必然超时。

坑在哪：
  1. **get 也算一次使用**。命中后必须把节点挪到表头，否则一个只被 get、
     从不被 put 的热键会慢慢沉到尾部被误淘汰。样例里第 4 次操作 get(1) 之后
     put(3,3) 淘汰的是 2 而不是 1，考的正是这一点；
  2. put 到已存在的 key 时只能**更新值并提到表头**，不能新建节点。新建会让字典指向
     新节点、链表里却还留着旧节点，容量统计和淘汰全部错乱；
  3. 淘汰必须在插入**之前**做。先插后删会在容量刚好用满时把刚写进去的新值又删掉；
  4. 链表节点里要存 key。淘汰时手上只有尾部那个节点，不存 key 就没法回头
     从字典里删掉对应条目，字典会无限膨胀、并且残留指向已摘除节点的死引用；
  5. 头尾哨兵不能省。省掉之后每次摘除都要判「它是不是表头/表尾」并改 self.head，
     分支立刻翻倍，也是这类题最常见的出错点；
  6. get 未命中返回 -1，这是题面规定的约定值，不是「不可能出现的值」——
     题面把 value 的范围限定在 0..10^5 正是为了让 -1 可以当哨兵用。

样例复核：
    capacity = 2。put(1,1)、put(2,2) 后链表为 2 -> 1（2 最新）。
    get(1) 返回 1 并把 1 提到表头，链表变 1 -> 2。
    put(3,3) 时已满，淘汰尾部的 2，链表变 3 -> 1；随后 get(2) 返回 -1。
    put(4,4) 淘汰尾部的 1，链表变 4 -> 3；get(1) 返回 -1，get(3) 返回 3，get(4) 返回 4。
    整串输出 [null,null,null,1,null,-1,null,-1,3,4]，与样例一致。
"""
from typing import List, Optional


class _Node:
    """双向链表的一个格子。

    key 必须一起存：淘汰尾部节点时手上只有节点对象，要靠它回头删掉字典里的条目。
    """
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.table = {}                  # key -> 链表节点，靠它把定位做到 O(1)
        # 头尾哨兵：真实节点永远夹在两者之间，摘除与插入因此不需要任何 None 判断
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: "_Node") -> None:
        # 摘除只改左右邻居的两个指针；有哨兵兜底，node 两侧必定存在
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node: "_Node") -> None:
        # 挂到头哨兵之后，表示「刚刚使用过」；四条指针的赋值顺序要先接新节点两侧
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        node = self.table.get(key)
        if node is None:
            return -1                    # 题面规定：关键字不存在时返回 -1
        # 读取同样算一次使用，必须提到表头，否则热键会被慢慢挤到尾部误淘汰
        self._remove(node)
        self._push_front(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        node = self.table.get(key)
        if node is not None:
            # 已存在只改值再提到表头；新建节点会让字典与链表指向两个不同对象
            node.value = value
            self._remove(node)
            self._push_front(node)
            return
        # 先淘汰再插入：反过来做会在容量刚好用满时把刚写进去的新值挤掉
        if len(self.table) >= self.capacity:
            lru = self.tail.prev         # 尾哨兵前面那个就是最久未使用的
            self._remove(lru)
            del self.table[lru.key]      # 靠节点里存的 key 反查并清理字典
        node = _Node(key, value)
        self.table[key] = node
        self._push_front(node)
