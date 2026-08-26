"""新增题单的覆盖面盘点：难度分布、标签分布、与既有 74 章的对接、题单之间的重题。

回答三个问题：
  1. 新增的 BM / LC 两套题，难度和考点分布长什么样，跟既有 165 题差在哪；
  2. 每道新题该挂到大纲的哪一章——挂不上的说明大纲缺章，得先补；
  3. BM 与 LC 有多少是同一道题（换个站换个名而已），能省多少工。

用法: uv run python scripts/audit_newsets.py
输出: dev/audit/新增题单覆盖盘点.md
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sol_store  # noqa: E402
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）
REPORT = AUDIT / "新增题单覆盖盘点.md"

# 官方标签 / 标题关键词 -> 章 id。一个考点可以命中多章，取全部。
# 写 id 而非章名：id 是永久主键（02 §3.2），章名改了也不会失配。
# P-M① 之前这里写的是章号，章号已经不进路径，也不再是稳定键。
# 待拆的超载章在拆完之前整体落在 new[0]，对应主题只能暂指源章；拆一章就回来重指一次。
# 已重指：单调队列 → ds/monotonic-queue（P-M② 第 4 步）。
# 已重指：分治 → basic/divide-conquer（P-M② 第 11 步）。
# 「回溯」指向 search/dfs 与 search/dlx，拆完 115 章后仍然成立，不必改。
TOPIC2CH = {
    "哈希表": ["python/dict", "ds/hash"], "哈希": ["ds/hash"], "字典": ["python/dict"],
    "数组": ["ds/array"], "矩阵": ["ds/array"], "链表": ["ds/linked-list"], "双向链表": ["ds/linked-list"],
    "栈": ["ds/stack"], "单调栈": ["ds/monotonic-stack"], "队列": ["ds/queue"], "单调队列": ["ds/monotonic-queue"],
    "堆（优先队列）": ["ds/heap"], "优先队列": ["ds/heap"], "堆": ["ds/heap"],
    "集合": ["python/set", "ds/multiset"], "并查集": ["ds/dsu"],
    "线段树": ["ds/fenwick"], "树状数组": ["ds/fenwick"], "区间最值查询": ["ds/fenwick", "basic/binary-lifting"],
    "有序集合": ["ds/balanced-tree"], "平衡树": ["ds/balanced-tree"],
    "排序": ["basic/sorting"], "快速排序": ["basic/sorting"], "归并排序": ["basic/sorting"], "桶排序": ["basic/discretization"],
    "计数": ["basic/discretization"], "计数排序": ["basic/discretization"], "基数排序": ["basic/sorting"],
    "前缀和": ["basic/prefix-sum"], "双指针": ["basic/two-pointer"], "滑动窗口": ["basic/two-pointer"],
    "二分查找": ["basic/binary-search"], "快速选择": ["basic/binary-search", "basic/sorting"],
    "位运算": ["python/operators", "basic/bit"], "贪心": ["basic/greedy"], "模拟": ["basic/simulation"], "博弈": ["math/game/impartial"],
    "分治": ["basic/divide-conquer", "technique/cdq"], "递归": ["python/function", "search/dfs"], "记忆化": ["search/memoization"], "记忆化搜索": ["search/memoization"],
    "深度优先搜索": ["search/dfs"], "广度优先搜索": ["search/bfs"], "回溯": ["search/dfs", "search/dlx"], "剪枝": ["search/memoization"],
    "字符串": ["python/string", "string/basic"], "字符串匹配": ["string/kmp"], "字典树": ["string/trie"], "回文": ["string/manacher"],
    "数学": ["math/recurrence"], "基础数学": ["math/recurrence"], "数论": ["math/number/basic"], "组合数学": ["math/combi/basic"],
    "快速幂": ["math/number/inverse"], "数论基础": ["math/number/basic"],
    "图": ["graph/basic"], "最短路": ["graph/shortest-path"], "最小生成树": ["graph/mst"], "拓扑排序": ["graph/topo"],
    "强连通分量": ["graph/scc"], "二分图": ["graph/topo"],
    "树": ["graph/tree/basic"], "二叉树": ["graph/tree/basic"], "二叉搜索树": ["graph/tree/basic", "ds/balanced-tree"], "树上算法": ["graph/tree/basic"],
    "动态规划": ["dp/basic"], "背包": ["dp/knapsack"], "线性DP": ["dp/linear"], "状态压缩": ["dp/interval"],
    "几何": ["geometry/basic"], "设计": ["python/oop-iterator"], "迭代器": ["python/oop-iterator"], "枚举": ["basic/simulation"],
    "有限状态机": ["dp/linear"], "数据流": ["ds/heap"], "前缀树": ["string/trie"], "拓扑": ["graph/topo"],
    "字符串哈希": ["ds/hash"], "滚动哈希": ["ds/hash"], "摩尔投票算法": ["basic/greedy"],
    "括号序列": ["ds/stack"], "多维动态规划": ["dp/interval"], "状态压缩动态规划": ["dp/interval"],
    "最长递增子序列": ["dp/linear", "math/order-theory"], "线段树数组": ["ds/fenwick"],
    # 两站的标签体系不统一：牛客爱写 "dfs"/"广度优先搜索(BFS)"，力扣写全称；
    # 还有一批是具体算法名而非考点名。都归到对应章，否则第 3 节会低估。
    "dfs": ["search/dfs"], "bfs": ["search/bfs"], "广度优先搜索(BFS)": ["search/bfs"], "深度优先搜索(DFS)": ["search/dfs"],
    "Floyd 判圈算法": ["ds/linked-list", "basic/two-pointer"], "Manacher 算法": ["string/manacher"],
    "背包问题": ["dp/knapsack"], "0-1 背包": ["dp/knapsack"], "完全背包": ["dp/knapsack"], "多重背包": ["dp/knapsack"],
    "二分": ["basic/binary-search"], "Binary Lifting": ["basic/binary-lifting"], "最近公共祖先": ["graph/tree/basic", "basic/binary-lifting"],
    "树形 DP": ["dp/interval"], "有向无环图": ["graph/topo"], "抽屉原理": ["math/combi/basic"],
    "最长上升子序列": ["dp/linear", "math/order-theory"], "最长公共子序列": ["dp/linear"],
    "冒泡排序": ["basic/sorting"], "锦标赛排序": ["basic/sorting", "ds/heap"],
    "X 算法": ["search/dlx"], "Brute-Force Search": ["basic/simulation"],
}
# 标题关键词兜底：官方标签为空时（牛客 BM 很多题没标签）靠标题猜
TITLE2CH = {
    "链表": ["ds/linked-list"], "反转": ["ds/linked-list"], "环": ["ds/linked-list"], "合并": ["basic/sorting"],
    "二叉树": ["graph/tree/basic"], "二叉搜索树": ["graph/tree/basic"], "树": ["graph/tree/basic"], "遍历": ["graph/tree/basic"],
    "排序": ["basic/sorting"], "查找": ["basic/binary-search"], "二分": ["basic/binary-search"], "栈": ["ds/stack"], "队列": ["ds/queue"],
    "堆": ["ds/heap"], "哈希": ["ds/hash"], "字符串": ["string/basic"], "回文": ["string/manacher"], "括号": ["ds/stack"],
    "背包": ["dp/knapsack"], "子序列": ["dp/linear"], "子数组": ["basic/prefix-sum", "dp/linear"], "子串": ["basic/two-pointer", "string/basic"],
    "路径": ["graph/tree/basic", "dp/interval"], "岛屿": ["search/bfs"], "矩阵": ["ds/array"], "滑动窗口": ["basic/two-pointer"],
    "全排列": ["search/dfs"], "组合": ["math/combi/basic"], "子集": ["search/dfs"], "括号生成": ["search/dfs"],
    "最短路": ["graph/shortest-path"], "拓扑": ["graph/topo"], "并查集": ["ds/dsu"], "前缀": ["basic/prefix-sum", "string/trie"],
    "股票": ["dp/linear"], "打家劫舍": ["dp/linear"], "爬楼梯": ["dp/basic"], "斐波那契": ["math/recurrence"],
    "数独": ["search/dlx"], "N皇后": ["search/dlx"], "皇后": ["search/dlx"], "字典树": ["string/trie"], "LRU": ["ds/linked-list", "python/dict"],
}


def load_chapters() -> dict:
    """章 id -> 例题数。P-M① 起 _mapping.json 是扁平的 {id: [题号]}。"""
    m = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))
    return {ch: len(qs) for ch, qs in m["chapters"].items()}


def guess_chapters(item: dict, by_no: dict) -> list:
    hits = []
    for t in item.get("tags") or []:
        hits += TOPIC2CH.get(t, [])
    if not hits:
        for kw, chs in TITLE2CH.items():
            if kw in item["title"]:
                hits += chs
    seen, out = set(), []
    for n in hits:
        if n not in seen and n in by_no:
            seen.add(n)
            out.append(n)
    return out


def norm_title(t: str) -> str:
    """归一化标题，用来找两套题单里的同一道题。"""
    t = re.sub(r"[【】\[\]（）()\s·、,，.。:：!！?？\"'-]", "", t)
    t = re.sub(r"(模板|的|中|个|II|III|IV|Ⅱ|Ⅲ|2|3)$", "", t)
    return t.lower()


def main() -> int:
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    sites, sets_ = d["sites"], [s for s in d["sets"] if (ROOT / s["list"]).exists()]
    by_no = load_chapters()
    data = {s["key"]: json.loads((ROOT / s["list"]).read_text(encoding="utf-8")) for s in sets_}

    L = ["# 新增题单覆盖盘点\n",
         "> 由 `scripts/audit_newsets.py` 生成。回答「新来的 201 题跟原有 165 题重不重、"
         "该挂到哪一章、大纲缺不缺章」。\n"]

    # ---------- 1. 规模与难度 ----------
    L += ["## 1　规模与难度分布\n",
          "| 题单 | 题数 | 判题模式 | " + " | ".join(["入门", "简单", "中等", "较难", "困难"]) + " |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    MODE = {"acm": "ACM", "core": "核心代码"}
    for s in sets_:
        c = Counter(it["difficulty"] for it in data[s["key"]])
        L.append(f"| {sites[s['site']]['name']} · {s['name']} | {len(data[s['key']])} | "
                 f"{MODE.get(s['mode'], s['mode'])} | "
                 + " | ".join(str(c.get(k, 0)) for k in ("入门", "简单", "中等", "较难", "困难")) + " |")
    L.append("")

    # ---------- 2. 两套新题单的重题 ----------
    new = [s for s in sets_ if s["key"] in ("bm", "hot100")]
    if len(new) == 2:
        a, b = data[new[0]["key"]], data[new[1]["key"]]
        idx = {}
        for it in a:
            idx.setdefault(norm_title(it["title"]), []).append(it)
        dup = []
        for it in b:
            for hit in idx.get(norm_title(it["title"]), []):
                dup.append((hit, it))
        L += [f"## 2　{new[0]['name']} 与 {new[1]['name']} 的重题\n",
              f"按标题归一化比对，**{len(dup)} 道是同一题**"
              f"（占 TOP101 的 {len(dup) / len(a) * 100:.0f}%、热题100 的 {len(dup) / len(b) * 100:.0f}%）。",
              "同一题两站都要交，但思路与题解正文可以复用，实际增量工作量按去重后算。\n",
              "| TOP101 | 力扣 | 标题 |", "| --- | --- | --- |"]
        for x, y in dup:
            L.append(f"| {x['no']} | {y['no']} | {y['title']} |")
        L.append("")

    # ---------- 3. 章节对接 ----------
    L += ["## 3　章节对接\n",
          "把每道新题按官方标签（标签为空时按标题关键词）映射到既有章节，"
          "看哪些章会变厚、哪些新题无处可挂。\n"]
    # 「新增(估)」只数**还没归属**的题（`meta.topics` 为空）。
    # 原实现数的是两套题单的全部 201 题，再与「现有例题」相加得出「合计」——
    # 归属一开始推进，同一道题就会在两列里各算一次，合计凭空变大。
    # 这是 09 教训二十二的形状：计数的前提「新题 ＝ 尚未归属的题」悄悄失效了，
    # 而报告仍自称是「还会增加多少」的估计。归属完的题已经落在「现有例题」里。
    assigned = {no for no, m in sol_store.load_all().items() if m.get("topics")}
    ch_add, orphan, done = Counter(), [], 0
    for s in new:
        for it in data[s["key"]]:
            if it["no"] in assigned:
                done += 1
                continue
            chs = guess_chapters(it, by_no)
            if not chs:
                orphan.append((s["key"], it))
            for n in chs:
                ch_add[n] += 1

    cur = by_no          # load_chapters() 已经是 {id: 例题数}

    total_new = sum(len(data[s["key"]]) for s in new)
    L += ["### 3.1 例题数变化最大的章\n",
          f"**「新增(估)」只数尚未归属的题**：两套题单共 {total_new} 题，"
          f"已归属 {done} 题落在「现有例题」列里不再重复计入，"
          f"剩 {total_new - done} 题参与估计。\n",
          "| 章节 | 现有例题 | 新增(估) | 合计 |", "| --- | --- | --- | --- |"]
    for n, add in ch_add.most_common(20):
        L.append(f"| {n} | {cur.get(n, 0)} | +{add} | {cur.get(n, 0) + add} |")
    if not ch_add:
        L.append("| （两套题单已全部归属） | — | — | — |")
    L.append("")

    thin = sorted(n for n in by_no if ch_add.get(n, 0) == 0)
    L += ["### 3.2 尚未归属的新题一道也接不到的章\n"]
    if not ch_add:
        # 归属推进到头时这一节会退化成「89 章全列出来」——那不是缺口清单，是噪声。
        # 本节的口径是「还没归属的题接不到哪些章」，没有题参与时它就不适用了。
        L += ["两套题单已全部归属，无题参与本节计数，本节暂不适用。\n"]
    else:
        L += [f"共 {len(thin)} 章。多为竞赛向专题——面试题单本来就不覆盖，属正常，不是缺口。"
              "**已归属的题不参与本节计数**，所以随着归属推进这一节会越列越多，"
              "那是进度不是退步。\n",
              "　".join(f"`{ch}`" for ch in thin) or "（无）", ""]

    L += ["### 3.3 挂不上任何章的新题\n",
          f"共 **{len(orphan)} 题**。这些要么是标签体系没覆盖的考点，要么需要新开章节，"
          "得逐题人工定归属。\n"]
    if orphan:
        L += ["| 题单 | 题号 | 标题 | 难度 | 官方标签 |", "| --- | --- | --- | --- | --- |"]
        for key, it in orphan:
            L.append(f"| {key} | {it['no']} | {it['title']} | {it['difficulty']} | "
                     f"{'、'.join(it['tags']) or '—'} |")
    L.append("")

    # ---------- 4. 力扣官方专题 ----------
    if "hot100" in data:
        g = Counter(it["group"] for it in data["hot100"])
        L += ["## 4　力扣官方专题分组\n",
              "力扣题单自带 17 个专题，是现成的学习顺序，可以直接当章节例题的补充索引。\n",
              "| 专题 | 题数 |", "| --- | --- |"]
        for name, n in g.most_common():
            L.append(f"| {name} | {n} |")
        L.append("")

    # ---------- 5. 标签缺口 ----------
    unknown = Counter()
    for s in new:
        for it in data[s["key"]]:
            for t in it.get("tags") or []:
                if t not in TOPIC2CH:
                    unknown[t] += 1
    if unknown:
        L += ["## 5　映射表没收录的官方标签\n",
              "出现在新题单里、但 `TOPIC2CH` 还没登记的标签。"
              "数量大的应当补进映射表，否则第 3 节的估算会偏低。\n",
              "| 标签 | 出现次数 |", "| --- | --- |"]
        for t, n in unknown.most_common(30):
            L.append(f"| {t} | {n} |")
        L.append("")

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"报告 -> {REPORT}")
    print(f"新增 {sum(len(data[s['key']]) for s in new)} 题，"
          f"挂不上章的 {len(orphan)} 题，未收录标签 {len(unknown)} 种")
    return 0


if __name__ == "__main__":
    sys.exit(main())
