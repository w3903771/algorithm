"""核心代码模式的序列化编解码：把题面样例的字符串还原成函数实参，把返回值还原成可比对的结构。

两家站点的写法不同，但类型词表已经统一（见 lc_fetch.py 与 nc_fetch_template.py），
所以这里按「方言 + 类型」两个维度处理，一套代码吃两家：

    力扣   JSON 写法，一行一个参数     [1,2,3] / null / "abc" / [["a","b"]]
    牛客   花括号表链表与树，# 表空    {1,2,3} / {1,#,2,3} / [3,2,4],6

比对不走字符串，走**结构**：两边都归一化成同一套 Python 结构再比。
这样 `{3,2,1}` 与 `[3,2,1]`、`["null","1"]` 与 `[null,1]` 都能正确判等——
牛客的设计题期望输出就是把 null 和数字全写成字符串的，按字面比一题都过不了。
"""
from __future__ import annotations

import json
import re
from collections import deque

LEETCODE = "leetcode"
NOWCODER = "nowcoder"


# --------------------------------------------------------------------------- #
# 判题双方都要用到的节点类型
# --------------------------------------------------------------------------- #

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        return f"ListNode({dump_list(self)})"


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({dump_tree(self)})"


class Interval:
    def __init__(self, start=0, end=0):
        self.start = start
        self.end = end


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class Node:
    """力扣「随机链表」用的节点：除 next 外还有一根 random 指针。

    牛客把同类节点叫 RandomListNode，力扣叫 Node。名字不同、结构一样，
    两边的题解都直接用判题环境注入的这个名字，所以两个名字都得给。
    """

    def __init__(self, x=0, next=None, random=None):
        self.val = self.label = x
        self.next = next
        self.random = random


class RandomListNode:
    def __init__(self, x=0):
        self.label = self.val = x
        self.next = None
        self.random = None


class TreeLinkNode:
    def __init__(self, x=0):
        self.val = x
        self.left = self.right = self.next = None


NODE_TYPES = {"ListNode": ListNode, "TreeNode": TreeNode, "Interval": Interval,
              "Point": Point, "RandomListNode": RandomListNode, "Node": Node,
              "TreeLinkNode": TreeLinkNode}


def build_list(seq):
    """[1,2,3] -> 1->2->3。空序列给 None，与两家站点的约定一致。"""
    head = cur = None
    for v in seq or []:
        node = ListNode(v)
        if head is None:
            head = cur = node
        else:
            cur.next = node
            cur = node
    return head


def dump_list(node) -> list:
    out, seen = [], set()
    while node is not None:
        if id(node) in seen:           # 题解写错成环时别把判题机吊死
            out.append("...cycle...")
            break
        seen.add(id(node))
        out.append(node.val)
        node = node.next
    return out


def build_tree(seq):
    """层序序列（空位是 None）-> 二叉树。两家的层序约定一致，只是空位写法不同。"""
    vals = list(seq or [])
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    q, i = deque([root]), 1
    while q and i < len(vals):
        node = q.popleft()
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                q.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                q.append(node.right)
    return root


def dump_tree(node) -> list:
    """二叉树 -> 层序序列，尾部的空位截掉（两家的期望输出都是截掉的）。"""
    if node is None:
        return []
    out, q = [], deque([node])
    while q:
        n = q.popleft()
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


# --------------------------------------------------------------------------- #
# 方言解析
# --------------------------------------------------------------------------- #

_NUM = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


class _Parser:
    """牛客写法的递归下降解析器。

    `{}` 与 `[]` 都当序列（牛客用 `{}` 表链表/树、`[]` 表数组，结构上没差别，
    真正的形状由参数类型决定）；`#` 与 `null` 都是空位。
    """

    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1

    def parse_seq(self, close: str) -> list:
        out = []
        self.ws()
        if self.i < len(self.s) and self.s[self.i] == close:
            self.i += 1
            return out
        while True:
            out.append(self.parse_value())
            self.ws()
            if self.i >= len(self.s):
                break
            if self.s[self.i] == ",":
                self.i += 1
                continue
            if self.s[self.i] == close:
                self.i += 1
                break
            break
        return out

    def parse_value(self):
        self.ws()
        if self.i >= len(self.s):
            return None
        ch = self.s[self.i]
        if ch == "{":
            self.i += 1
            return self.parse_seq("}")
        if ch == "[":
            self.i += 1
            return self.parse_seq("]")
        if ch in "\"'":
            return self.parse_string(ch)
        # 裸词：数字、true/false、null、#，或没加引号的字符串
        j = self.i
        while j < len(self.s) and self.s[j] not in ",]}":
            j += 1
        tok = self.s[self.i:j].strip()
        self.i = j
        return atom(tok)

    def parse_string(self, quote: str) -> str:
        self.i += 1
        buf = []
        while self.i < len(self.s):
            ch = self.s[self.i]
            if ch == "\\" and self.i + 1 < len(self.s):
                nxt = self.s[self.i + 1]
                buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
                self.i += 2
                continue
            if ch == quote:
                self.i += 1
                break
            buf.append(ch)
            self.i += 1
        return "".join(buf)


def atom(tok: str):
    if tok in ("#", "null", "NULL", "None", ""):
        return None
    if tok in ("true", "True"):
        return True
    if tok in ("false", "False"):
        return False
    if _NUM.match(tok):
        return float(tok) if any(c in tok for c in ".eE") else int(tok)
    return tok


def parse_nowcoder(text: str) -> list:
    """牛客的一整行输入 -> 顶层参数列表。`[3,2,4],6` 切成两个参数。"""
    p = _Parser(text or "")
    out = []
    while True:
        p.ws()
        if p.i >= len(p.s):
            break
        out.append(p.parse_value())
        p.ws()
        if p.i < len(p.s) and p.s[p.i] == ",":
            p.i += 1
            continue
        if p.i < len(p.s):
            break
    return out


def parse_value(text: str, dialect: str):
    """单个值：力扣是合法 JSON，牛客走自己的解析器。"""
    text = (text or "").strip()
    if dialect == LEETCODE:
        try:
            return json.loads(text)
        except ValueError:
            return atom(text)
    vals = parse_nowcoder(text)
    return vals[0] if len(vals) == 1 else vals


def split_params(text: str, nparams: int, dialect: str) -> list:
    """样例输入 -> nparams 个原始值（还没按类型塑形）。

    力扣一行一个参数；牛客全挤在一行、用顶层逗号分隔。
    `nparams` 传 0 或 None 表示「有几个取几个」——设计题就是这么用的，
    它的参数个数由操作序列决定，不由签名决定。
    """
    if dialect == LEETCODE:
        lines = [l for l in (text or "").replace("\r\n", "\n").split("\n")]
        return [parse_value(l, dialect) for l in (lines[:nparams] if nparams else lines)]
    vals = parse_nowcoder(text)
    return vals[:nparams] if nparams else vals


# --------------------------------------------------------------------------- #
# 按类型塑形
# --------------------------------------------------------------------------- #

def shape(value, type_: str):
    """把解析出来的裸结构按声明类型塑形（主要是把序列变成链表 / 树）。"""
    t = (type_ or "").strip()
    if t == "ListNode":
        return build_list(value)
    if t == "TreeNode":
        return build_tree(value)
    # 牛客的 Java 泛型归一成 `list<X>`，力扣的写法是 `X[]`，两种别名都得认——
    # 只认一种的话 BM5（签名是 list<ListNode>）会把「列表的列表」原样传给题解
    if t in ("ListNode[]", "list<ListNode>"):
        return [build_list(v) for v in value or []]
    if t in ("TreeNode[]", "list<TreeNode>"):
        return [build_tree(v) for v in value or []]
    if t == "Interval":
        return Interval(*(value or [0, 0]))
    if t == "Interval[]" or t == "list<Interval>":
        return [Interval(*(v or [0, 0])) for v in value or []]
    if t == "Point[]" or t == "list<Point>":
        return [Point(*(v or [0, 0])) for v in value or []]
    if t == "character" and isinstance(value, str) and value:
        return value[0]
    if t in ("integer", "long") and isinstance(value, float) and value.is_integer():
        return int(value)
    if t == "double" and isinstance(value, int):
        return float(value)
    return value


def to_args(text: str, params: list, dialect: str) -> list:
    raw = split_params(text, len(params), dialect)
    while len(raw) < len(params):
        raw.append(None)
    return [shape(v, p.get("type")) for v, p in zip(raw, params)]


# --------------------------------------------------------------------------- #
# 归一化与比对
# --------------------------------------------------------------------------- #

def to_canon(value):
    """任意返回值 -> 可 JSON 序列化的规范结构（链表/树摊成序列）。"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, ListNode):
        return dump_list(value)
    if isinstance(value, TreeNode):
        return dump_tree(value)
    if isinstance(value, Interval):
        return [value.start, value.end]
    if isinstance(value, Point):
        return [value.x, value.y]
    if isinstance(value, (list, tuple)):
        return [to_canon(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((to_canon(v) for v in value), key=repr)
    if isinstance(value, dict):
        return {str(k): to_canon(v) for k, v in value.items()}
    return str(value)


def encode(value, type_: str = None):
    """返回值 -> 规范结构，按**声明的返回类型**编码。

    不能只看运行时类型：空链表和空树都是 `None`，可两家的期望输出都写作
    `[]` / `{}` 而不是 `null`。只有拿到声明类型才知道这个 None 该编成空序列
    （LC206 的第三个样例、BM1 的第二个样例就卡在这里）。
    """
    t = (type_ or "").strip()
    if t == "ListNode":
        return dump_list(value)
    if t == "TreeNode":
        return dump_tree(value)
    if t in ("ListNode[]", "list<ListNode>"):
        return [dump_list(v) for v in value or []]
    if t in ("TreeNode[]", "list<TreeNode>"):
        return [dump_tree(v) for v in value or []]
    return to_canon(value)


def canon(value):
    """比对前的宽松归一化。

    牛客的期望输出常把 null 和数字都写成字符串（设计题的
    `["null","null","1"]`），按字面比一题都过不了；力扣的 `true/false`
    与牛客的 `"true"` 也是同一回事。所以这里把「看起来是什么」当成什么。
    """
    if isinstance(value, str):
        return atom(value.strip())
    if isinstance(value, (list, tuple)):
        return [canon(v) for v in value]
    if isinstance(value, dict):
        return {str(k): canon(v) for k, v in value.items()}
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def equal(a, b, eps: float = 0.0) -> bool:
    a, b = canon(a), canon(b)
    return _eq(a, b, eps)


def _eq(a, b, eps: float) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_eq(x, y, eps) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k], eps) for k in a)
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if eps and a != b:
            return abs(a - b) <= eps * max(1.0, abs(b))
        return a == b
    return a == b


def _key(v):
    """给无序比较用的稳定排序键：类型名 + JSON 文本，避免 int 与 str 相互比较报错。"""
    return (type(v).__name__, json.dumps(v, sort_keys=True, ensure_ascii=False, default=str))


def equal_unordered(a, b, eps: float = 0.0) -> bool:
    """顶层顺序无关（LC46 全排列、LC347 前 K 个高频元素这类）。"""
    a, b = canon(a), canon(b)
    if not (isinstance(a, list) and isinstance(b, list)):
        return _eq(a, b, eps)
    if len(a) != len(b):
        return False
    rest = list(b)
    for x in a:
        for i, y in enumerate(rest):
            if _eq(x, y, eps):
                rest.pop(i)
                break
        else:
            return False
    return True


def equal_unordered_deep(a, b, eps: float = 0.0) -> bool:
    """内外层都顺序无关（LC49 字母异位词分组、LC78 子集这类嵌套列表）。"""
    a, b = canon(a), canon(b)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        sa = sorted((sorted(x, key=_key) if isinstance(x, list) else x for x in a), key=_key)
        sb = sorted((sorted(y, key=_key) if isinstance(y, list) else y for y in b), key=_key)
        return _eq(sa, sb, eps)
    return _eq(a, b, eps)


CMP = {
    "exact": equal,
    "unordered": equal_unordered,
    "unordered_deep": equal_unordered_deep,
}
