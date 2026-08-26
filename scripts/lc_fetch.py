"""抓取力扣「热题 100」学习计划 -> sources/06-leetcode/

产物与牛客那边同构，好让下游（gen_index / build_pages / verify）一套逻辑吃两家：
  hot100_list.json / .md          题单清单（字段与 nc 的 *_list.json 对齐）
  raw/LC<题号>.json               机器可读的题面 + 样例 + 函数签名
  problems/LC<题号>.md            人读的题面

题号用**力扣真实题号**（LC1 / LC206 / LC1143），与 leetcode.cn/problems/<slug> 一一对应，
因此不连续；牛客那三套题单的题号是连续的，两者不冲突也不必强行统一。

与牛客最大的不同：
  1. 力扣是**核心代码模式**，没有 stdin。样例的机器可读输入来自 `exampleTestcases`
     （一行一个参数，按参数个数分组），函数签名来自 `metaData`。
  2. **接口不给期望输出**。`exampleTestcases` 只有输入，`输出：` 得从题面 HTML 的
     <pre> 示例块里解析。所以两边都要抓，再按顺序配对，配不上就记 warning。

用法:
  uv run python scripts/lc_fetch.py             # 题单 + 全部题面
  uv run python scripts/lc_fetch.py --list      # 只刷新题单
  uv run python scripts/lc_fetch.py two-sum     # 只抓指定 slug（调试用）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lc_common import gql, html_to_md  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "06-leetcode"
RAW = OUT / "raw"
MD = OUT / "problems"
for d in (OUT, RAW, MD):
    d.mkdir(parents=True, exist_ok=True)

PLAN_SLUG = "top-100-liked"
PLAN_URL = f"https://leetcode.cn/studyplan/{PLAN_SLUG}/"
SLUG = "hot100"

# 难度词表跟牛客对齐（牛客用 入门/简单/中等/较难/困难）
DIFF = {"EASY": "简单", "MEDIUM": "中等", "HARD": "困难",
        "Easy": "简单", "Medium": "中等", "Hard": "困难"}

PLAN_Q = """
query studyPlanDetail($slug: String!) {
  studyPlanV2Detail(planSlug: $slug) {
    slug name
    planSubGroups {
      slug name questionNum
      questions { titleSlug title translatedTitle questionFrontendId difficulty paidOnly
                  topicTags { name nameTranslated slug } }
    }
  }
}"""

DETAIL_Q = """
query questionDetail($slug: String!) {
  question(titleSlug: $slug) {
    questionId questionFrontendId title translatedTitle difficulty
    translatedContent content
    metaData exampleTestcases sampleTestCase stats
    topicTags { name translatedName slug }
    codeSnippets { langSlug code }
    hints
  }
}"""


# --------------------------------------------------------------------------- #
# 题单
# --------------------------------------------------------------------------- #

def fetch_list() -> list:
    j = gql(PLAN_Q, {"slug": PLAN_SLUG}, "plan", use_cache=False)
    plan = ((j.get("data") or {}).get("studyPlanV2Detail")) or {}
    items = []
    for g in plan.get("planSubGroups") or []:
        for q in g.get("questions") or []:
            fid = q["questionFrontendId"]
            items.append({
                "no": f"LC{fid}",
                "title": q.get("translatedTitle") or q["title"],
                "titleEn": q["title"],
                "questionId": fid,
                "uuid": q["titleSlug"],           # 力扣这边「uuid」就是 titleSlug
                "tpId": PLAN_SLUG,
                "group": g["name"],               # 官方分组：哈希 / 双指针 / …
                "groupSlug": g["slug"],
                "difficulty": DIFF.get(q["difficulty"], q["difficulty"]),
                "acceptRate": 0.0,                # 题单接口不给，抓详情时回填
                "paidOnly": bool(q.get("paidOnly")),
                # 题单接口给的是 CommonTagNode(nameTranslated)，详情接口是 TopicTagNode(translatedName)
                "tags": [t.get("nameTranslated") or t["name"] for t in (q.get("topicTags") or [])],
                "url": f"https://leetcode.cn/problems/{q['titleSlug']}/",
            })
    items.sort(key=lambda it: int(it["questionId"]))
    return items


def write_list(items: list) -> None:
    (OUT / f"{SLUG}_list.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    groups = {}
    for it in items:
        groups.setdefault(it["group"], []).append(it)
    L = ["# 力扣 热题 100 题目清单\n",
         f"> planSlug={PLAN_SLUG}，共 {len(items)} 题，官方分 {len(groups)} 组  ",
         f"> 入口: {PLAN_URL}\n",
         "| 编号 | 题目 | 分组 | 难度 | 通过率 | 标签 | 链接 |",
         "| --- | --- | --- | --- | --- | --- | --- |"]
    for it in items:
        L.append(f"| {it['no']} | {it['title']} | {it['group']} | {it['difficulty']} | "
                 f"{it['acceptRate']}% | {'、'.join(it['tags'])} | [练习]({it['url']}) |")
    (OUT / f"{SLUG}_list.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# 题面与样例
# --------------------------------------------------------------------------- #

_KEYS = ("输入", "输出", "解释", "说明", "Input", "Output", "Explanation")
# 冒号是可选的：设计题的老 <pre> 写法把「输入」单独占一行，后面才跟数据
_KEY_RE = re.compile(r"^[ \t]*(?:\*\*)?(" + "|".join(_KEYS) + r")(?:\*\*)?[ \t]*[:：]?[ \t]*", re.M)


def _is_example_block(tag) -> bool:
    if tag.name == "pre":
        return True
    return tag.name == "div" and "example-block" in (tag.get("class") or [])


def _block_text(tag) -> str:
    """把一个示例容器压成「一行一个字段」的纯文本，好让 _KEY_RE 按行切。

    <pre> 本来就是按行摆的，直接取文本；而新版 example-block 是一堆 <p>，
    键与值分处 <strong> 内外（`<p><strong>输入：</strong>nums = [1,2]</p>`），
    所以段内必须用空格拼、段间才换行——否则「输入：」会和它的值断成两行。
    """
    if tag.name == "pre":
        text = tag.get_text("\n")
    else:
        parts = tag.find_all(["p", "ul", "ol", "pre", "div"], recursive=False)
        text = "\n".join(p.get_text(" ").strip() for p in (parts or [tag]))
    return text.replace("\r\n", "\n").replace("\xa0", " ")


def parse_examples(html: str) -> list:
    """从题面 HTML 里解析出 [{raw_input, output, note}]。

    力扣中文站同时并存三种示例写法，都要认：
      1. 老版 <pre><strong>输入：</strong>nums = [2,7], target = 9 …</pre>
      2. 新版 <div class="example-block"><p><strong>输入：</strong>…</p>…</div>
         （键有时包在 <span class="example-io"><b>输入：</b>…</span> 里）
      3. 设计题的 <pre>，「输入」独占一行、不带冒号，后面跟操作序列与参数两行
    `输出：` 后面可能跨多行，所以按「下一个关键字出现处」切，而不是按行切。
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "lxml")
    out = []
    for tag in soup.find_all(_is_example_block):
        # example-block 里可能再套 <pre>，只认最外层，否则同一个示例会被数两遍
        if any(_is_example_block(p) for p in tag.parents if getattr(p, "name", None)):
            continue
        text = _block_text(tag)
        hits = list(_KEY_RE.finditer(text))
        if not hits:
            continue
        fields = {}
        for i, m in enumerate(hits):
            end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
            # 冒号有时写在 <strong> 外头（`<b>输入</b>: nums = …`），键的正则吃不到，这里再剥一次
            fields.setdefault(m.group(1), text[m.end():end].strip().lstrip(":：").strip())
        got_in = fields.get("输入") or fields.get("Input")
        got_out = fields.get("输出") or fields.get("Output")
        if got_out is None:
            continue
        out.append({
            "raw_input": got_in or "",
            "output": got_out,
            "note": fields.get("解释") or fields.get("说明") or fields.get("Explanation") or "",
        })
    return out


# 题面写法 `nums = [1,2], target = 9` 里的「形参名 =」分隔符
_ARG_SEP = re.compile(r"(?:^|,)\s*[A-Za-z_]\w*\s*=\s*")


def _squash(s: str) -> str:
    """比对用的归一化：题面爱把矩阵换行排版、字符用单引号，语义上与 testcase 无差别。"""
    return re.sub(r"\s+", "", s or "").replace("'", '"')


def inputs_agree(raw_input: str, testcase: str) -> bool:
    """题面示例的输入与 exampleTestcases 的这一组是不是同一个。"""
    vals = [v.strip() for v in _ARG_SEP.split(raw_input or "") if v.strip()]
    lines = [l.strip() for l in (testcase or "").split("\n") if l.strip()]
    if len(vals) != len(lines):
        return False
    return all(_squash(a) == _squash(b) for a, b in zip(vals, lines))


def pair_examples(blocks: list, inputs: list, design: bool) -> tuple:
    """把题面示例（有期望输出）与 exampleTestcases（有机器可读输入）配起来。

    **不能按下标硬配**：两边数量常常不等——官方 testcase 里有题面没展示的用例
    （LC94 就多一个），题面里也有纯图片的示例（LC62）。按下标配会把甲的输入
    配上乙的期望输出，而且一声不响，后面拿它当判题基准就全错了。
    所以优先按输入内容匹配，匹配不上才退回下标，并且照实记 warning。

    设计题的题面输入是「操作序列 + 参数」两块，不走 `形参 = 值` 的写法，
    内容匹配无从谈起，直接按下标配。
    """
    examples, warn, used = [], [], set()
    for i, b in enumerate(blocks):
        j = None
        if not design:
            j = next((k for k in range(len(inputs))
                      if k not in used and inputs_agree(b["raw_input"], inputs[k])), None)
        aligned = j is not None
        if j is None:                       # 内容配不上，退回下标
            j = i if i < len(inputs) and i not in used else None
        if j is None:
            warn.append(f"示例{i + 1} 无机器可读输入，判题跑不了")
            continue
        used.add(j)
        if design:
            aligned = True
        elif not aligned:
            warn.append(f"示例{i + 1} 输入与 testcase 对不上，期望输出可能错位")
        examples.append({"name": f"示例{i + 1}", "input": inputs[j],
                         "output": b["output"], "note": b["note"],
                         "raw_input": b["raw_input"], "aligned": aligned})
    extra = [k for k in range(len(inputs)) if k not in used]
    if extra:
        warn.append(f"{len(extra)} 个官方 testcase 题面没给期望输出，已忽略")
    return examples, warn


def split_testcases(example_testcases: str, nparams: int) -> list:
    """`exampleTestcases` 是「一行一个参数」拼起来的，按参数个数切成一组组。"""
    if not example_testcases or nparams <= 0:
        return []
    lines = example_testcases.replace("\r\n", "\n").split("\n")
    return ["\n".join(lines[i:i + nparams]) for i in range(0, len(lines), nparams)]


def func_info(meta_data: str) -> dict:
    """从 metaData 里读出函数签名。区分普通函数题与设计题（有 classname）。"""
    try:
        md = json.loads(meta_data or "{}")
    except ValueError:
        return {"kind": "unknown", "nparams": 0, "meta": {}}
    if md.get("classname"):
        # 设计题：判题输入固定是「操作名数组 + 参数数组」两行。
        # constructor / methods 要提到顶层——牛客那边的 func 就是这个形状，
        # 下游（new_solution.py 生成骨架）按统一结构读，不该去挖各站的 meta。
        return {"kind": "design", "classname": md["classname"], "nparams": 2,
                "constructor": md.get("constructor") or {"params": []},
                "methods": md.get("methods") or [],
                "meta": md}
    return {"kind": "function", "name": md.get("name"),
            "params": md.get("params") or [], "return": md.get("return") or {},
            "nparams": len(md.get("params") or []), "meta": md}


def to_md(meta: dict, d: dict) -> str:
    L = [f"# {meta['no']} {d.get('title') or meta['title']}\n",
         f"> 来源: [{meta['url']}]({meta['url']})  ",
         f"> 分组: {meta['group']}　难度: {meta['difficulty']}　通过率: {meta['acceptRate']}%　"
         f"标签: {'、'.join(meta['tags']) or '无'}  ",
         f"> 模式: 核心代码（{d['func'].get('kind')}）"
         + (f"　签名: `{d['func'].get('name')}`" if d["func"].get("name") else ""), ""]
    L.append("## 题目描述\n")
    L.append(d.get("description") or "_(未抓到)_")
    for i, ex in enumerate(d.get("examples") or [], 1):
        L.append(f"\n## 示例{i}\n")
        if ex.get("raw_input"):
            L.append("**输入**（题面写法）\n")
            L.append("```\n" + ex["raw_input"] + "\n```\n")
        L.append("**输入**（判题用）\n")
        L.append("```\n" + ex["input"] + "\n```\n")
        L.append("**输出**\n")
        L.append("```\n" + ex["output"] + "\n```")
        if ex.get("note"):
            L.append("\n**说明**\n")
            L.append(ex["note"])
    if d.get("snippet"):
        L.append("\n## 代码模板\n")
        L.append("```python\n" + d["snippet"].rstrip() + "\n```")
    return "\n".join(L) + "\n"


def fetch_detail(meta: dict) -> dict:
    j = gql(DETAIL_Q, {"slug": meta["uuid"]}, "detail")
    q = (j.get("data") or {}).get("question")
    if not q:
        return {}
    fn = func_info(q.get("metaData"))
    inputs = split_testcases(q.get("exampleTestcases") or "", fn["nparams"])
    blocks = parse_examples(q.get("translatedContent") or q.get("content") or "")

    examples, warn = pair_examples(blocks, inputs, fn["kind"] == "design")

    snippet = next((c["code"] for c in (q.get("codeSnippets") or [])
                    if c["langSlug"] == "python3"), "")
    # 提交接口要的是**内部** questionId，不是题号（questionFrontendId）。
    # 题单接口不给，只能抓详情时顺手记下来，否则 lc_submit 每题都得多打一次接口。
    meta["internalId"] = str(q.get("questionId") or "")
    try:
        meta["acceptRate"] = round(float((json.loads(q.get("stats") or "{}")
                                          .get("acRate") or "0").rstrip("%")), 2)
    except (ValueError, AttributeError):
        pass
    return {
        "title": q.get("translatedTitle") or q["title"],
        "titleEn": q["title"],
        "description": html_to_md(q.get("translatedContent") or q.get("content") or ""),
        "inputDesc": "", "outputDesc": "", "otherDesc": {},
        "examples": examples,
        "func": fn,
        "snippet": snippet,
        "hints": q.get("hints") or [],
        "warnings": warn,
        "meta": meta,
    }


def main(argv) -> int:
    only = [a for a in argv[1:] if not a.startswith("-")]
    list_only = "--list" in argv[1:]

    lp = OUT / f"{SLUG}_list.json"
    if lp.exists() and only and not list_only:
        items = json.loads(lp.read_text(encoding="utf-8"))
    else:
        print(f"== 抓题单 {PLAN_SLUG}")
        items = fetch_list()
        write_list(items)
        print(f"  -> {len(items)} 题")
        if list_only:
            return 0

    todo = [it for it in items if not only or it["uuid"] in only or it["no"] in only]
    ok = fail = skip = 0
    for it in todo:
        raw_p = RAW / f"{it['no']}.json"
        if raw_p.exists() and not only:
            skip += 1
            continue
        d = fetch_detail(it)
        if not d or not d.get("description"):
            print(f"  [FAIL] {it['no']} {it['title']}")
            fail += 1
            continue
        raw_p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        (MD / f"{it['no']}.md").write_text(to_md(d["meta"], d), encoding="utf-8")
        ok += 1
        if d["warnings"]:
            print(f"  [warn] {it['no']} {it['title']}: {'; '.join(d['warnings'])}")
        if ok % 10 == 0:
            print(f"  ... 已抓 {ok} 题 (最新 {it['no']} {it['title']})")

    # acceptRate 是抓详情时才回填的，抓完重写一遍题单
    if not only:
        write_list(items)
    print(f"[hot100] 成功 {ok}，跳过(已存在) {skip}，失败 {fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
