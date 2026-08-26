"""核心代码模式判题链路的自测：拿真实题面 + 参考实现，跑完整 harness。

**这里的实现是测试夹具，不是题解。** 它们只写进临时目录，跑完就删，
`solutions/` 下不会留下任何 BM/LC 文件。夹具挑的都是最短最没悬念的写法，
目的是证明「喂参 → 调用 → 取返回值 → 比对」这条链路对，而不是证明算法好。

覆盖的是 harness 里最容易出错的几处：

  两种方言        力扣 `[1,2,3]` / 牛客 `{1,2,3}`、`{1,#,2,3}`
  链表与树        参数方向（序列 -> 节点）与返回方向（节点 -> 序列）都要对
  返回 void       答案在入参里（LC283 移动零），读返回值只会拿到 None
  设计题          力扣「首位是 null」与牛客「构造参数在末尾」两套约定
  自定义驱动器    BM39/42/43/48 那种签名里看不出调用顺序的题
  顺序无关比对    unordered / unordered_deep

用法: uv run python scripts/test_corejudge.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify  # noqa: E402

# --------------------------------------------------------------------------- #
# 夹具：题号 -> (判题配置, 参考实现)
# --------------------------------------------------------------------------- #

FIXTURES = {
    # ---- 力扣：普通函数、返回数组，多解（下标顺序不定）----
    "LC1": ({"mode": "unordered"}, '''
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, v in enumerate(nums):
            if target - v in seen:
                return [seen[target - v], i]
            seen[v] = i
        return []
'''),
    # ---- 力扣：链表进、链表出 ----
    "LC206": ({}, '''
class Solution:
    def reverseList(self, head):
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev
'''),
    # ---- 力扣：树进、数组出（含 null 空位）----
    "LC94": ({}, '''
class Solution:
    def inorderTraversal(self, root):
        out, stack = [], []
        while root or stack:
            while root:
                stack.append(root)
                root = root.left
            root = stack.pop()
            out.append(root.val)
            root = root.right
        return out
'''),
    # ---- 力扣：返回 void，答案留在入参里 ----
    "LC283": ({}, '''
class Solution:
    def moveZeroes(self, nums):
        j = 0
        for i, v in enumerate(nums):
            if v:
                nums[i], nums[j] = nums[j], nums[i]
                j += 1
'''),
    # ---- 力扣：嵌套列表，内外层顺序都不定 ----
    "LC49": ({"mode": "unordered_deep"}, '''
class Solution:
    def groupAnagrams(self, strs):
        g = {}
        for s in strs:
            g.setdefault("".join(sorted(s)), []).append(s)
        return list(g.values())
'''),
    # ---- 力扣：设计题，ops[0] 是构造，输出首位是 null ----
    "LC146": ({}, '''
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.d = OrderedDict()

    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap:
            self.d.popitem(last=False)
'''),
    # ---- 牛客：链表，方言是 {1,2,3} ----
    "BM1": ({}, '''
class Solution:
    def ReverseList(self, head):
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev
'''),
    # ---- 牛客：多参数挤在一行，`[3,2,4],6` ----
    "BM50": ({}, '''
class Solution:
    def twoSum(self, numbers, target):
        seen = {}
        for i, v in enumerate(numbers, 1):
            if target - v in seen:
                return [seen[target - v], i]
            seen[v] = i
        return []
'''),
    # ---- 牛客：树用 {1,#,2,3} 表空位，返回嵌套列表 ----
    "BM26": ({}, '''
class Solution:
    def levelOrder(self, root):
        out, cur = [], [root] if root else []
        while cur:
            out.append([n.val for n in cur])
            cur = [c for n in cur for c in (n.left, n.right) if c]
        return out
'''),
    # ---- 牛客：设计题，构造参数在输入末尾，输出与 ops 一一对应 ----
    "BM100": ({}, '''
from collections import OrderedDict

class Solution:
    def __init__(self, capacity):
        self.cap = capacity
        self.d = OrderedDict()

    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]

    def set(self, key, value):
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap:
            self.d.popitem(last=False)
'''),
    # ---- 牛客：自定义驱动器，参数编在操作名里 ----
    "BM42": ({}, '''
class Solution:
    def __init__(self):
        self.a, self.b = [], []

    def push(self, node):
        self.a.append(node)

    def pop(self):
        if not self.b:
            while self.a:
                self.b.append(self.a.pop())
        return self.b.pop()
'''),
    # ---- 牛客：自定义驱动器，输出是格式化后的单个字符串 ----
    "BM48": ({}, '''
import bisect

class Solution:
    def __init__(self):
        self.a = []

    def Insert(self, num):
        bisect.insort(self.a, num)

    def GetMedian(self):
        n = len(self.a)
        return self.a[n // 2] if n % 2 else (self.a[n // 2 - 1] + self.a[n // 2]) / 2.0
'''),
    # ---- 牛客：自定义驱动器，两个方法咬合（序列化一个来回）----
    "BM39": ({}, '''
class Solution:
    def Serialize(self, root):
        out = []

        def go(n):
            if not n:
                out.append("#")
                return
            out.append(str(n.val))
            go(n.left)
            go(n.right)

        go(root)
        return ",".join(out)

    def Deserialize(self, s):
        it = iter(s.split(","))

        def go():
            t = next(it)
            if t == "#":
                return None
            n = TreeNode(int(t))
            n.left, n.right = go(), go()
            return n

        return go()
'''),
}


def main() -> int:
    index = verify.load_index()
    tmp = Path(tempfile.mkdtemp(prefix="corejudge_"))
    rows, bad = [], 0
    try:
        for no, (conf, src) in FIXTURES.items():
            if no not in index:
                rows.append((no, "SKIP", "题面 JSON 没抓，先跑对应的 fetch 脚本"))
                continue
            f = tmp / f"{no}.py"
            f.write_text(src.lstrip(), encoding="utf-8")
            r = verify.run_one(no, {no: conf}, index, sol=f)
            ok = r["status"] == "PASS"
            bad += not ok
            detail = r.get("detail", "")
            if r.get("fails"):
                i, kind, inp, exp, got = r["fails"][0]
                detail = f"样例{i} {kind} 期望 {exp!r} 实得 {got!r}"[:160]
            rows.append((no, r["status"], f"{r.get('mode', '-')}　{r.get('cases', 0)} 样例　{detail}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    width = max(len(r[0]) for r in rows)
    for no, status, detail in rows:
        mark = {"PASS": " ok ", "SKIP": "skip"}.get(status, "FAIL")
        print(f"[{mark}] {no:<{width}}  {status:<12} {detail}")
    total = sum(1 for r in rows if r[1] != "SKIP")
    print(f"\n{total - bad} / {total} 通过")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
