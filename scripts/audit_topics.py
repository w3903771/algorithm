"""知识点 → 章 → 例题的贯通性审计，输出 dev/audit/知识点贯通审计.md。

现有的三个审计各管一段，**没有一个走完整条链**：

| 脚本 | 管的那一段 |
| --- | --- |
| `audit_sources.py` | 知识点 → 章（有没有认领） |
| `audit_depth.py` | 章内讲没讲透（anchors） |
| `audit_outline.py` | 题 → 章（有没有归属）、章有没有例题、需求有没有承接 |
| **本脚本** | **整条链**：知识点 → 章存在 → 章有例题 → 例题被正文引用 → 例题拿到判定 |

区别在于**它报的是「链在第几环断的」**。「某知识点有章、章也有例题，
但那道例题正文一次没提」——上面三个脚本各自都看不出这一条，
因为它跨了两段：`audit_outline` 只到「章有例题」，`check_orphan` 只从题往回看。

知识点有三个来源，都读：

| 来源 | 在哪 | 条数 |
| --- | --- | --- |
| 用户需求清单 | `_mapping.json` 的 `required_topics` | 48 |
| 本地资料知识点 | `_source_topics.json` | 169 |
| OI-wiki 分类学 355 条 | `_topics.json` | **P0c 的产出**，存在就读，不存在就跳过 |

第三份不存在时报告里会明说「未接入」——**不写清楚的话，下一批会以为 355 条已经在管了**。

本脚本有两个模式（Q15 定死，07 §5）：

| 模式 | 做什么 | 写报告的哪一节 |
| --- | --- | --- |
| 贯通性（默认） | 知识点 → 章存在 → 章有例题 → 例题被正文引用 → 例题有判定，报「断在第几环」 | `MARK` 之前 |
| `--new` 差集 | 读 OI-wiki 的 nav（**只读 nav，不读正文**，07 §1 红线），报「OI-wiki 有而 `_topics.json` 未登记」 | `MARK` 之后 |

**两个模式写同一份报告，各自只重写自己那一节**（`split_report()`）。
原先只有 `--new` 保留贯通性那半，反方向没挡——跑一次裸的本脚本就会把差集那 415 行
静默删掉（09 教训十九，P0c② 实测被咬）。P0c③ 把两个方向都补上了。

--------------------------------------------------------------------------
本脚本看不见什么
--------------------------------------------------------------------------
1. **知识点清单本身漏了什么**。它只走清单里有的那些。355 条那一份 P0c 才有，
   在那之前「覆盖率」这个词只能相对前两份清单说。
2. **讲得对不对**。链条每一环都是「在不在」，不是「好不好」。
   讲透与否归 `audit_depth.py` 的 anchors。
3. **例题配得合不合适**。「这一章挂了三道题」它认，「这三道题跟本章知识点没关系」它不认。
4. **一个知识点需要几道例题**。有一道就算通。够不够是人的判断。
5. **`docs/` 之外**。题解正文、附录索引都不算「正文引用」，口径与
   `check_orphan.py` 一致（生成页整份跳过）。
6. **判读判得对不对**（`--new` 模式）。它只查「登记了没有」，不查「这一档判得合不合理」。
   `inclusion` 的复核靠人，且 07 §3.1 的主依据（近 5 年省选 / NOI 频次）要 P3 才有数据。
7. **`planned` 指向的章还不存在**（`--new` 模式）。那是天花板清单里的名字，不是磁盘上的文件；
   本脚本只核对 `chapters` 里的现存章，`planned` 一律不查存在性。

用法: uv run python scripts/audit_topics.py
      uv run python scripts/audit_topics.py -v     # 逐条打印链条判定
      uv run python scripts/audit_topics.py --new  # 与 OI-wiki 355 条比差集
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布
DEV_DATA = ROOT / "dev" / "data"   # 开发侧数据：不随本仓库发布，clone 的检出里没有这个目录
AUDIT = ROOT / "dev" / "audit"      # 脚本生成的报告：P-M② 起在 dev/audit/（02 §7.3）

REPORT = AUDIT / "知识点贯通审计.md"
TOPICS = DEV_DATA / "_topics.json"      # P0c 的产出
OIWIKI = ROOT / "sources" / "OI-wiki" / "mkdocs.yml"   # 只读它的 nav（07 §1 红线）
# OI-wiki nav 里取算法性 section、剔 index 页，得 355 条（07 §2.1）
OI_SECTIONS = ("basic", "search", "ds", "dp", "graph", "string",
               "math", "geometry", "misc", "topic")
INCLUSIONS = ("core", "ext", "ref", "out")

sys.path.insert(0, str(ROOT / "scripts"))
import check_orphan  # noqa: E402   引用扫描只有它一份实现，别在这儿再写一遍
import check_prose  # noqa: E402   「什么算正文」的归口（front-matter 不算），别在这儿再判一遍
import sol_store  # noqa: E402

LINKS = ["章存在", "章有例题", "例题被正文引用", "例题有判定"]

# 两个模式写**同一份**报告：贯通性写 MARK 之前那几节，`--new` 写 MARK 之后那一节。
# 谁都不许把对方那半冲掉——09 教训十九：闸门是只读的，**它写的报告不是**。
# P0c② 就是跑了一次裸的本脚本，把 `--new` 那 415 行静默删掉了。
MARK = "\n## 与 OI-wiki 分类学的差集（`--new`）"


def split_report() -> tuple[str, str]:
    """把现有报告切成（贯通性那半, 差集那半）。文件不存在时两半都是空串。

    两个模式各自只重写自己那半，另一半原样搬回去。
    """
    cur = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    if MARK in cur:
        head, tail = cur.split(MARK, 1)
        return head.rstrip(), MARK + tail
    return cur.rstrip(), ""


def oiwiki_topics() -> dict:
    """OI-wiki nav 里的 355 条算法知识点：{key: {sec, path, name, nav}}。

    **只读 nav，不读正文**（07 §1 红线）。

    key 就是 nav 里的显示名，但 nav 里有重名——「基本概念」在「抽象代数」与「概率论」
    下各有一条。重名时 key 后缀父级 nav 目录消歧（「基本概念（概率论）」）。
    这条规则只有这一份实现：_topics.json 的键由它生成，差集也用它比对，
    两边各写一遍必然漂移。
    """
    try:
        import yaml
    except ImportError:                       # 干净环境没有 pyyaml
        raise SystemExit("--new 需要 pyyaml（mkdocs 的依赖）：uv run python scripts/audit_topics.py --new")
    if not OIWIKI.is_file():
        raise SystemExit(
            "找不到 %s——sources/OI-wiki/ 已 gitignore，"
            "跑差集前先按 README 把它 clone 回来（07 §1）" % OIWIKI.relative_to(ROOT))

    class L(yaml.SafeLoader):
        pass
    # OI-wiki 的 mkdocs.yml 用了 !!python/name: 标签，SafeLoader 认不得，忽略掉
    L.add_multi_constructor("tag:yaml.org,2002:python/name:", lambda *a: None)
    nav = yaml.load(OIWIKI.read_text(encoding="utf-8"), Loader=L)["nav"]

    flat = []                                  # [(父级 nav 路径, 显示名, 文件)]

    def walk(node, path):
        if isinstance(node, list):
            for x in node:
                walk(x, path)
        elif isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    flat.append((path, k, v))
                else:
                    walk(v, path + [k])
    walk(nav, [])

    sel = [(pa, nm, f) for pa, nm, f in flat
           if f.split("/")[0] in OI_SECTIONS and not f.split("/")[-1].startswith("index")]
    seen = {}
    for _, nm, _f in sel:
        seen[nm] = seen.get(nm, 0) + 1
    out = {}
    for pa, nm, f in sel:
        key = "%s（%s）" % (nm, pa[-1]) if seen[nm] > 1 and pa else nm
        out[key] = {"sec": f.split("/")[0], "path": f, "name": nm, "nav": " / ".join(pa)}
    return out


def prose_hits(aliases: list, text: dict) -> int:
    """按归一化关键词数正文命中（07 §2.1 的初筛口径）。

    这个数**不写进 _topics.json**——它是派生量，每次现算（教训七）。
    """
    return sum(t.count(a) for t in text.values() for a in aliases)


def diff_new(argv: list) -> int:
    """--new：与 OI-wiki 355 条比差集，报未登记 / 档分布 / 命中数实测。"""
    oi = oiwiki_topics()
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))
    on_disk = set(mapping["chapters"])
    # **剥掉 front-matter 再数**（09 教训二十二）。P1① 给 89 章补了
    # `id:` / `title:` 两行元信息，按关键词计数就成了「这一章讲了线段树」——
    # 实测给 69 条知识点注水 87 处，差点把 P1① 真正删掉的 93 处遮住。
    # front-matter 是机器可读的声明，不是正文，不能当「正文有讲」的证据。
    text = {c: check_prose.strip_front_matter(
                (DOCS / (c + ".md")).read_text(encoding="utf-8"))
            for c in on_disk if (DOCS / (c + ".md")).is_file()}

    reg = {}
    if TOPICS.exists():
        reg = {k: v for k, v in json.loads(TOPICS.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}

    unreg = sorted(set(oi) - set(reg), key=lambda k: (oi[k]["sec"], oi[k]["path"]))
    own = sorted(set(reg) - set(oi))
    bad_ch = [(k, c) for k, v in sorted(reg.items())
              for c in v.get("chapters", []) if c not in on_disk]
    by_inc = {i: [] for i in INCLUSIONS}
    other_inc = []
    for k, v in sorted(reg.items()):
        (by_inc[v["inclusion"]] if v.get("inclusion") in by_inc else other_inc).append(k)
    # 登记为 core/ext 却一章未挂：贯通性模式按 chapters 走链，会跳过它们——
    # 跳过不等于没问题，在这里点名（教训四）
    homeless = sorted(k for k, v in reg.items()
                      if v.get("inclusion") in ("core", "ext")
                      and not v.get("chapters") and not v.get("planned"))
    ch_exist = {c for v in reg.values()
                if v.get("inclusion") in ("core", "ext") for c in v.get("chapters", [])}
    ch_plan = {v["planned"] for v in reg.values()
               if v.get("inclusion") in ("core", "ext") and v.get("planned")} - on_disk

    L = ["", "## 与 OI-wiki 分类学的差集（`--new`）", "",
         "> 只读 `sources/OI-wiki/mkdocs.yml` 的 nav，**不读它的正文**（07 §1 红线）。", "",
         "OI-wiki nav 的算法性条目 **%d** 条；`_topics.json` 已登记 **%d** 条；"
         % (len(oi), len(reg)),
         "**未登记 %d 条**——必须补登记，哪怕定为 `ref` / `out`。" % len(unreg), "",
         "| 项 | 数 |", "| --- | --- |",
         "| OI-wiki 有、`_topics.json` 无（未登记） | **%d** |" % len(unreg),
         "| `_topics.json` 有、OI-wiki 无（本项目独有，正常） | %d |" % len(own),
         "| 登记的 `chapters` 指向磁盘上没有的章 | **%d** |" % len(bad_ch),
         "| 登记为 core/ext 却一章未挂 | **%d** |" % len(homeless), "",
         "### 已登记条目的档分布", "",
         "| 档 | 条数 | 处理（07 §3） |", "| --- | --- | --- |"]
    desc = {"core": "独立章或独立小节，配例题",
            "ext": "并入相关章的一节，配 0–1 题",
            "ref": "只进附录 D 知识点总表，一句话定位，不写正文",
            "out": "不收录，登记理由"}
    for i in INCLUSIONS:
        L.append("| `%s` | %d | %s |" % (i, len(by_inc[i]), desc[i]))
    if other_inc:
        L.append("| **非法档** | %d | %s |" % (len(other_inc), "、".join(other_inc)))
    # 与 02 §5 的天花板比时**必须先对齐口径**（Q17 结案时踩过一次）：
    # 上面两个数只覆盖「被某条 core/ext 知识点指到的章」，而磁盘上还有一批章
    # 没有任何 core/ext 知识点指着——python/ 的语法章、toolkit/io、ds/multiset、
    # dp/linear 本来就不在 OI-wiki 分类学里，**但它们照样占章数**。
    # 只报 172 而 02 §5 的天花板是 218，会读成「逼近上限」，实际差得远。
    unmapped = sorted(on_disk - ch_exist)
    total = len(ch_exist | ch_plan) + len(unmapped)
    L += ["",
          "core ＋ ext 指向的章：现存 **%d** ＋ 尚未落地 **%d** = **%d**。"
          % (len(ch_exist), len(ch_plan), len(ch_exist | ch_plan)),
          "另有 **%d** 章在磁盘上、却没有任何 `core`/`ext` 知识点指着"
          "（不在 OI-wiki 分类学里，但照样占章数）：%s。"
          % (len(unmapped), "、".join("`%s`" % c for c in unmapped) or "无"),
          "",
          "> **合计 %d 章——要和 02 §5 的天花板（218）比，就比这一行。**"
          " 上面那个「= %d」只数本文件登记到的那部分，拿它去比天花板会低估"
          "（Q17 结案时踩过一次：报 172 被读成「逼近 212」，实际是 %d 对 218）。"
          % (total, len(ch_exist | ch_plan), total),
          "> 章数的唯一口径是 02 §5。", ""]

    if bad_ch:
        L += ["### 登记的章不在磁盘上", ""] + ["- `%s` → `%s`" % kv for kv in bad_ch] + [""]
    if homeless:
        L += ["### 登记为 core/ext 却一章未挂", "",
              "贯通性模式按 `chapters` 走链，会**跳过**这些条目，所以在这里点名，"
              "免得被当成「已经在管了」。", ""] + ["- %s" % k for k in homeless] + [""]

    L += ["### 未登记的 %d 条" % len(unreg), ""]
    if unreg:
        cur = None
        for k in unreg:
            if oi[k]["sec"] != cur:
                cur = oi[k]["sec"]
                L += ["", "**%s**" % cur, ""]
            L.append("- %s" % k)
        L.append("")
    else:
        L += ["无——355 条全部登记。", ""]

    if own:
        L += ["### `_topics.json` 有、OI-wiki 无", "", "本项目独有的知识点，正常。", ""]
        L += ["- %s" % k for k in own] + [""]

    L += ["### 命中数实测", "",
          "按每条登记的 `aliases` 现算，**不写进 `_topics.json`**（教训七：派生的数字要生成）。",
          "记了 `prose-zero` 却有命中、记了 `prose-covered` 却零命中，都在这里现形。", "",
          "| 知识点 | 档 | 依据类型 | 正文命中 |", "| --- | --- | --- | --- |"]
    drift = 0
    for k, v in sorted(reg.items(), key=lambda kv: (kv[1].get("sec", ""), kv[0])):
        n = prose_hits(v.get("aliases", []), text)
        b = set(v.get("basis", []))
        flag = ""
        if "prose-zero" in b and n:
            flag = " ⚠ 记了 prose-zero"
        elif "prose-covered" in b and n == 0:
            flag = " ⚠ 记了 prose-covered"
        elif v.get("inclusion") == "core" and "prose-covered" in b and n < 5:
            flag = " ⚠ core 的 prose-covered 要求 ≥5 处"
        drift += bool(flag)
        L.append("| %s | `%s` | %s | %d%s |"
                 % (k, v.get("inclusion"), "、".join(sorted(b)), n, flag))
    L += ["", "与登记的依据类型不符：**%d** 条。" % drift, ""]

    head, _ = split_report()               # 贯通性那半原样留着
    REPORT.write_text(head + "\n" + "\n".join(L), encoding="utf-8")

    for k, c in bad_ch:
        print("[章不存在] %s -> %s" % (k, c))
    for k in homeless:
        print("[一章未挂] %s" % k)
    print("OI-wiki %d 条：已登记 %d、未登记 %d；本项目独有 %d"
          % (len(oi), len(reg), len(unreg), len(own)))
    print("档分布　" + "、".join("%s %d" % (i, len(by_inc[i])) for i in INCLUSIONS)
          + ("、非法 %d" % len(other_inc) if other_inc else ""))
    print("core+ext 指向的章 %d（现存 %d ＋ 未落地 %d）；"
          "加上无 core/ext 承接的 %d 章，合计 %d —— 和 02 §5 的天花板比要用合计"
          % (len(ch_exist | ch_plan), len(ch_exist), len(ch_plan),
             len(unmapped), total))
    print("依据类型与实测不符 %d 条" % drift)
    print("报告：%s" % REPORT.relative_to(ROOT))
    # 未登记不算失败——P0c 分三个子批次做，中途本来就有未登记的
    return 1 if (bad_ch or other_inc or drift) else 0



def load_topics(mapping: dict) -> list:
    """`[(来源, 知识点, [章 id])]`，三份清单合起来。"""
    out = []
    for topic, chs in mapping["required_topics"].items():
        if not topic.startswith("_"):
            out.append(("需求清单", topic, list(chs)))

    src = json.loads((DEV_DATA / "_source_topics.json").read_text(encoding="utf-8"))
    for group, items in src.items():
        if group == "_comment":
            continue
        for topic, cfg in items.items():
            if cfg.get("excluded") or not cfg.get("chapter"):
                continue
            out.append((group, topic, [cfg["chapter"]]))

    if TOPICS.exists():
        d = json.loads(TOPICS.read_text(encoding="utf-8"))
        for topic, cfg in d.items():
            if topic.startswith("_") or not cfg.get("chapters"):
                continue
            out.append(("OI-wiki 355", topic, list(cfg["chapters"])))
    return out


def chain_audit(argv: list) -> int:
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))
    chapters = mapping["chapters"]
    topics = load_topics(mapping)

    refs, _, _ = check_orphan.scan()          # 题号 -> 正文引用处
    metas = sol_store.load_all()
    judged = {no for no, m in metas.items()
              if ((m.get("langs") or {}).get("py") or {}).get("status")}

    # ---- 逐条走链
    rows, broken = [], {k: [] for k in LINKS}
    for source, topic, chs in topics:
        alive = [c for c in chs if (DOCS / (c + ".md")).is_file()]
        probs = [q for c in alive for q in chapters.get(c, [])]
        cited = [q for q in probs if refs.get(q)]
        ok = [q for q in cited if q in judged]

        if not alive:
            stage = "章存在"
        elif not probs:
            stage = "章有例题"
        elif not cited:
            stage = "例题被正文引用"
        elif not ok:
            stage = "例题有判定"
        else:
            stage = ""
        if stage:
            broken[stage].append((source, topic, chs))
        rows.append((source, topic, chs, len(alive), len(probs), len(cited), len(ok), stage))

    # ---- 反向：没有任何知识点落在它上面的章
    claimed = {c for _, _, chs in topics for c in chs}
    unclaimed = sorted(set(chapters) - claimed)

    AUDIT.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for r in rows if not r[7])
    L = ["# 知识点贯通审计", "",
         "> 由 `scripts/audit_topics.py` 生成。**不要手改本文件。**", "",
         "走的是整条链：**知识点 → 章存在 → 章有例题 → 例题被正文引用 → 例题拿到判定**，",
         "报的是「链在第几环断的」。前三个审计脚本各管一段，没有一个跨得过两段。", "",
         f"知识点 **{len(topics)}** 条：全链通过 **{passed}**、断链 **{len(topics) - passed}**。", "",
         "| 断在哪一环 | 条数 | 性质 |", "| --- | --- | --- |"]
    # 「N 个章暂无例题」现算，不写死——它随每一批归属往下掉（教训七）。
    # 08 §6.3 第 2 条的口径是**盯章数不盯条数**：断链条数会因为多条知识点
    # 指向同一个空章而放大，章数才是真正要清的那个量。
    empty_ch = sorted({c for _, _, chs in topics for c in chs
                       if c in chapters and not chapters[c]})
    nature = {
        "章存在": "**新问题**——清单指向一个磁盘上没有的章",
        "章有例题": f"已知待办（Q7：**{len(empty_ch)}** 个章暂无配套例题，"
                    f"P1② / P4 / P5 补。**盯章数不盯条数**）",
        "例题被正文引用": "**新问题**——章挂了题，正文一次没提（`check_orphan.py` 的甲档）",
        "例题有判定": "已知待办——例题还没过判题机",
    }
    for k in LINKS:
        L.append(f"| {k} | **{len(broken[k])}** | {nature[k]} |")

    L += ["", "## 知识点清单的三个来源", "",
          "| 来源 | 条数 | 状态 |", "| --- | --- | --- |"]
    by_src: dict = {}
    for r in rows:
        by_src[r[0]] = by_src.get(r[0], 0) + 1
    for s, n in sorted(by_src.items()):
        L.append(f"| {s} | {n} | 已接入 |")
    if not TOPICS.exists():
        L.append("| OI-wiki 分类学 355 条 | — | **未接入**：`dev/data/_topics.json` "
                 "是 P0c 的产出，现在还不存在。在它落地之前，本报告的覆盖率"
                 "只相对前两份清单成立 |")
    else:
        # 「已接入 N 条」里的 N 是**能走链的**条数，不是登记条数——
        # 本模式按 chapters 走链，一章未挂的（ref/out 与还没落地的 planned）走不了。
        # 两个数不写清楚，下一批会把 63 当成 115（教训四：先说清看不见什么）。
        reg = {k: v for k, v in json.loads(TOPICS.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        walkable = by_src.get("OI-wiki 355", 0)
        L.append(f"| ↑ 其中 OI-wiki 那份 | 登记 {len(reg)} / 355 | "
                 f"能走链的只有 **{walkable}** 条——本模式按 `chapters` 走，"
                 "挂现存章的才算；`ref` / `out` 与 `planned` 还没落地的走不了。"
                 "登记进度与未登记清单见 `--new` 那一节 |")
    L.append("")

    for k in LINKS:
        items = broken[k]
        L += [f"## 断在「{k}」（{len(items)} 条）", "", nature[k], ""]
        if items:
            L += ["| 来源 | 知识点 | 声明的章 |", "| --- | --- | --- |"]
            L += [f"| {s} | {t} | {'、'.join(f'`{c}`' for c in chs)} |" for s, t, chs in items]
        else:
            L.append("无。")
        L.append("")

    L += ["## 没有任何知识点落在它上面的章", "",
          "不一定是问题：拆分拆出来的新章、目录页承接的选型表都可能这样。",
          "但**新写一章却忘了把知识点挂上去**也长这样，所以列出来看一眼。", ""]
    L += [f"- `{c}`（例题 {len(chapters[c])} 道）" for c in unclaimed] or ["无。"]
    L.append("")
    _, tail = split_report()               # 差集那半原样留着（教训十九：反方向同样要挡）
    REPORT.write_text("\n".join(L).rstrip() + "\n" + tail, encoding="utf-8")

    if "-v" in argv:
        for s, t, chs, na, np_, nc, nk, stage in rows:
            print(f"{'断@' + stage if stage else '通过　'}\t{t}\t{chs}\t"
                  f"章{na} 题{np_} 引用{nc} 判定{nk}")
    for k in ("章存在", "例题被正文引用"):
        for s, t, chs in broken[k]:
            print(f"[断@{k}] {t} -> {chs}")

    print(f"知识点 {len(topics)} 条：全链通过 {passed}、断链 {len(topics) - passed}　"
          + "、".join(f"{k} {len(broken[k])}" for k in LINKS))
    print(f"无知识点承接的章 {len(unclaimed)} 个")
    print(f"报告：{REPORT.relative_to(ROOT)}")
    # 只有「章存在」与「例题被正文引用」两环算新问题，另两环是已登记待办
    return 1 if (broken["章存在"] or broken["例题被正文引用"]) else 0


def main(argv: list) -> int:
    """贯通性总是先跑一遍：两个模式写同一份报告，先跑贯通性才不会把差集那一节冲掉。"""
    rc = chain_audit(argv)
    if "--new" in argv:
        print("-" * 60)
        rc = diff_new(argv) or rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
