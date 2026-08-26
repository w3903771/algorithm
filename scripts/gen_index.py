"""生成附录 A（题单总索引）、README 的进度表、dev/notes/章节对照表.md，
并同步各目录索引页的章数与例题数。

把「题号 / 标题 / 难度 / 官方标签 / 所属章节 / 题解状态」汇成一张表，
数据来自 data/_sources.json 登记的各题单 JSON + data/_mapping.json + solutions/_verify_report.md，
章节显示名取自 mkdocs.yml 的 nav 标签——章路径自 P-M① 起是 id，不带章号也不带中文。
所以永远和实际状态同步，不会写成过期的手工表格。

题单不再硬编码：新增一套题单只改 data/_sources.json，这里与 hooks/build_pages.py 都自动跟上。

用法: uv run python scripts/gen_index.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sol_store as store  # noqa: E402

ROOT = store.ROOT
DOCS = ROOT / "docs"
DATA = store.DATA                   # 公开数据：见 sol_store.DATA
SOL = store.SOL
OUT = DOCS / "appendix" / "a-problems.md"
MAP_OUT = ROOT / "dev" / "notes" / "章节对照表.md"   # 源码树里查「这个英文 slug 是哪一章」

NO = re.compile(r"[A-Z]+\d+")


def load_sources() -> tuple:
    d = json.loads((DATA / "_sources.json").read_text(encoding="utf-8"))
    return d["sites"], [s for s in d["sets"] if (ROOT / s["list"]).exists()]


def load_verify() -> dict:
    """从验证报告里读出每题的通过状态。"""
    p = SOL / "_verify_report.md"
    if not p.exists():
        return {}
    st = {}
    for line in p.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"\|\s*([A-Z]+\d+)\s*\|\s*([^|]+)\|", line)
        if m:
            st[m.group(1)] = m.group(2).strip()
    return st


# 章号单独捕一组：拆章产生的新章用「源章号 + 字母」（39A / 39B / 39C），
# 这样不必重排现有 74 章的号——正文里还有大量「见 62-记忆化搜索与剪枝」
# 这类带章号的引用，那批清洗是 P1 的活，现在重排会把正文说错。
NAV_ROW = re.compile(r"^\s+- (?:(\d+[A-Z]?)\s*·\s*)?(.+?): (\S+\.md)\s*$")


def chapter_titles() -> dict:
    """章 id -> 中文标题。取自 mkdocs.yml 的 nav 标签，去掉前面的章号。

    章号只活在 nav 标签里（02 §3.3：章号不进文件名，第 N 章由 nav 顺序生成）。

    **P1① 已给 89 章补上 front-matter 的 `title`**（原注说「直到 P2」，批次记错了）。
    两处的值现在一模一样——本函数生成 front-matter 时就是从 nav 标签剥的章号前缀。
    没有改成读 front-matter，是因为**章号仍然只有 nav 有**：`_split_label()` 还要
    用它排序与显示，读 front-matter 只能拿到标题、拿不到章号，得同时读两处。
    真要归一，得等 02 §3.3 的「第 N 章由 nav 顺序生成」这条本身被替换掉。
    """
    out, in_nav = {}, False
    for line in (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines():
        if line.rstrip() == "nav:":
            in_nav = True
            continue
        if not in_nav:
            continue
        m = NAV_ROW.match(line)
        if m and not m.group(3).endswith("/index.md"):
            out[m.group(3)[:-len(".md")]] = m.group(2)
    return out


def volume_counts() -> dict:
    """卷号 -> 章数，读**各章 front-matter 的 `volume`**。

    口径故意与 `hooks/build_pages.py` 的 `_walk_volumes()` **不同**：
    那边数的是 nav 顶层分组，这边数的是 front-matter 的声明。
    两者本该永远相等，而「本该相等的两个口径」正是最容易悄悄分叉的地方——
    有人往 nav 里挪一章却忘了改 front-matter，站点与 README 就会各说各话。
    所以不去合并它们，而是让 `check_decisions` 的 `volume_counts_agree`
    把**分歧本身**当成一个指标盯着（09 教训二十六）。
    """
    out: dict = {}
    for f in sorted(DOCS.rglob("*.md")):
        if f.name == "index.md" or f.relative_to(DOCS).parts[0] == "appendix":
            continue
        m = re.search(r"^volume:\s*(\d+)\s*$", f.read_text(encoding="utf-8"), re.M)
        if m:
            out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def chapter_numbers() -> dict:
    """章 id -> nav 标签里的章号（`39` / `39A`）。没写章号的返回空串。"""
    out, in_nav = {}, False
    for line in (ROOT / "mkdocs.yml").read_text(encoding="utf-8").splitlines():
        if line.rstrip() == "nav:":
            in_nav = True
            continue
        if not in_nav:
            continue
        m = NAV_ROW.match(line)
        if m and not m.group(3).endswith("/index.md"):
            out[m.group(3)[:-len(".md")]] = m.group(1) or ""
    return out


def write_chapter_map(mapping: dict, titles: dict) -> None:
    """把「章 id -> 中文标题」写成一份表，放在 dev/notes/ 供维护者查阅。

    章标题的唯一来源是 mkdocs.yml 的 nav 标签（见 chapter_titles），
    所以这份表必须生成、不能手写——手写的一定会和 nav 走散。
    站点侧的同一份数据在附录 A 的「按章节反查」表里。
    """
    nums = chapter_numbers()
    by_dir = {}
    for ch in mapping["chapters"]:
        by_dir.setdefault(ch.split("/")[0], []).append(ch)
    L = ["# 章节对照表\n",
         "> 由 `scripts/gen_index.py` 自动生成，**不要手改**。",
         "> 数据来自 `mkdocs.yml` 的 nav 标签——那是章标题唯一的存放处",
         "> （章号不进文件名、中文标题不进路径，见 02 号文件 §3）。\n",
         "`docs/` 下的路径用英文 slug，因为它同时是**站点 URL** 与 **`id` 永久主键**：",
         "改一个 slug 就要改 URL、重定向表、`_mapping.json` 与全部站内链接。",
         "中文只活在 nav 标签、正文 H1 与本表里——**在源码树里认章就查这一份**。\n",
         "共 **{}** 章。\n".format(len(mapping["chapters"]))]
    for folder in sorted(by_dir):
        L.append("## `{}/`\n".format(folder))
        L.append("| 章号 | 中文标题 | 源文件 |")
        L.append("| --- | --- | --- |")
        for ch in by_dir[folder]:
            L.append("| {} | {} | `docs/{}.md` |".format(
                nums.get(ch) or "—", titles.get(ch, ch), ch))
        L.append("")
    MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    MAP_OUT.write_text("\n".join(L) + "\n", encoding="utf-8")


def folder_titles() -> dict:
    """顶层目录 -> 中文名，取各目录索引页的一级标题。

    源码树里目录名是英文 slug（`ds` / `basic`），那是 URL 兼 id（02 §3）；
    面向读者的名字只有目录索引页的 `# 数据结构` 那一行有。
    不另开一份映射表——多一份就多一处会漂的东西（09 教训七）。
    """
    out = {}
    for f in sorted(DOCS.glob("*/index.md")):
        for line in f.read_text(encoding="utf-8").split("\n"):
            if line.startswith("# "):
                out[f.parent.name] = line[2:].strip()
                break
    return out


def sync_dir_index(mapping: dict) -> None:
    """改写 docs/<目录>/index.md 里的「本部分 N 章，配套 M 道牛客真题」。

    这两个数字原先是手写的，P-M① 的锁定复核发现 6 个目录页与页内章节盘自相矛盾
    （toolkit 5→4、ds 10→11、basic 11→10、search 3→4、math 6→10、graph 5→8）。
    手写的数字每拆一次章就会走样一次，索性生成——**M 按章节盘右侧数字之和计**，
    也就是「章-题对」的个数，读者把那一列加起来就该得到这个数。
    """
    chs, qs = {}, {}
    for ch, problems in mapping["chapters"].items():
        top = ch.split("/")[0]
        chs[top] = chs.get(top, 0) + 1
        qs[top] = qs.get(top, 0) + len(problems)
    pat = re.compile(r"本部分 \*\*\d+ 章\*\*，配套 \*\*\d+ 道\*\*")
    for folder, n in sorted(chs.items()):
        f = DOCS / folder / "index.md"
        if not f.exists():
            # 静默跳过会让「数字由脚本保证」这条承诺出现盲区：
            # 缺索引页的目录既不在章节盘里正常成组，也拿不到生成的数字。
            print("  ⚠ %s/ 有 %d 章却没有 index.md，章节盘会退指第一章" % (folder, n))
            continue
        t = f.read_text(encoding="utf-8")
        new = "本部分 **{} 章**，配套 **{} 道**".format(n, qs.get(folder, 0))
        t2 = pat.sub(new, t, count=1)
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            print("  索引页 {}/index.md -> {} 章 / {} 道".format(folder, n, qs.get(folder, 0)))


def main() -> int:
    sites, sets_ = load_sources()
    titles = chapter_titles()
    mapping = json.loads((DATA / "_mapping.json").read_text(encoding="utf-8"))
    # P-M① 起 _mapping.json 是扁平的 {id: [题号]}，顺序即原章号顺序
    q2ch = {}
    for ch, qs in mapping["chapters"].items():
        for q in qs:
            q2ch.setdefault(q, []).append(titles.get(ch, ch))

    # 站点构建期要用的题目元信息（sources/ 不入库，hooks/build_pages.py 读这份）
    problems = {}
    for s in sets_:
        for it in json.loads((ROOT / s["list"]).read_text(encoding="utf-8")):
            problems[it["no"]] = {
                "title": it["title"], "url": it["url"],
                "difficulty": it["difficulty"], "acceptRate": it["acceptRate"],
                "tags": it["tags"],
                # 来源信息随题目一起入库，构建期不必再回头读 sources/
                "set": s["key"], "site": s["site"], "mode": s["mode"],
                **({"group": it["group"]} if it.get("group") else {}),
            }
    (DATA / "_problems.json").write_text(
        json.dumps(problems, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    verify = load_verify()
    by_set, done, has_sol, total = {}, 0, 0, 0
    for s in sets_:
        rows = []
        for it in json.loads((ROOT / s["list"]).read_text(encoding="utf-8")):
            no = it["no"]
            sol = store.sol_path(no)
            total += 1
            if sol.exists():
                has_sol += 1
            v = verify.get(no, "")
            ok = "PASS" in v
            if ok:
                done += 1
            status = "✅ 已验证" if ok else ("⚠️ " + v if v else ("📝 已写" if sol.exists() else "—"))
            rows.append({
                "no": no, "title": it["title"], "diff": it["difficulty"],
                "tags": "、".join(it["tags"]) or "—", "group": it.get("group", ""),
                "chs": q2ch.get(no, []), "status": status, "url": it["url"],
                "has_sol": sol.exists(),
            })
        by_set[s["key"]] = rows

    L = ["# 附录 A　题单总索引\n",
         "> 由 `scripts/gen_index.py` 自动生成，数据来自 `data/_sources.json` 登记的各题单、",
         "> 章节映射与验证报告，因此始终与仓库实际状态一致。\n",
         f"**共 {total} 题　已写题解 {has_sol} 题　通过官方样例 {done} 题**\n",
         "| 来源 | 题单 | 题数 | 判题模式 | 已写 | 已验证 |",
         "| --- | --- | --- | --- | --- | --- |"]
    MODE = {"acm": "ACM（stdin）", "core": "核心代码"}
    for s in sets_:
        rows = by_set[s["key"]]
        w = sum(r["has_sol"] for r in rows)
        d = sum("✅" in r["status"] for r in rows)
        L.append(f"| [{sites[s['site']]['name']}]({sites[s['site']]['url']}) | {s['name']} | "
                 f"{len(rows)} | {MODE.get(s['mode'], s['mode'])} | {w} | {d} |")
    L.append("")

    for s in sets_:
        rows = by_set[s["key"]]
        site = sites[s["site"]]
        L += [f"## {site['name']}　{s['name']}\n",
              f"{s['desc']}　题号段：{s['range']}　共 **{len(rows)} 题**　"
              f"入口：[{site['fullName']}]({site['url']})\n",
              # q-table 让站点给这些长表挂上即时筛选框（docs/javascripts/table-filter.js）
              '<div class="q-table" markdown>', ""]
        has_group = any(r["group"] for r in rows)
        head = "| 题号 | 标题 |" + (" 专题 |" if has_group else "") + " 难度 | 官方标签 | 讲解章节 | 题解 |"
        L += [head, "| --- | --- |" + (" --- |" if has_group else "") + " --- | --- | --- | --- |"]
        for r in rows:
            chs = "、".join(r["chs"]) if r["chs"] else "—"
            sol = (f"[{r['status']}](../solutions/{r['no']}.md)"
                   if r["has_sol"] else r["status"])
            grp = f" {r['group']} |" if has_group else ""
            L.append(f"| [{r['no']}]({r['url']}) | {r['title']} |{grp} {r['diff']} | "
                     f"{r['tags']} | {chs} | {sol} |")
        L += ["", "</div>", ""]

    # 按章节反查
    L.append("## 按章节反查\n")
    L.append("| 章节 | id | 例题 |")
    L.append("| --- | --- | --- |")
    for ch, qs in mapping["chapters"].items():
        L.append(f"| {titles.get(ch, ch)} | `{ch}` | {'、'.join(qs) or '—'} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    # 历史文件名：A-牛客题单总索引 →（题单不再只有牛客）A-题单总索引
    # →（P-M① 改 id 路径）a-problems。留下的旧文件清掉。
    for name in ("A-牛客题单总索引.md", "A-题单总索引.md"):
        old = OUT.parent / name
        if old.exists() and old != OUT:
            old.unlink()

    # 章节对照表：docs/ 的路径是英文 slug（它就是 URL 兼 id，02 §3），
    # 在源码树里认不出是哪一章。这份表把 id 与中文标题并排列出，随 nav 自动重生成。
    write_chapter_map(mapping, titles)

    sync_dir_index(mapping)

    # 同步 README 进度表
    readme = ROOT / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        # 按顶层目录汇总。目录不再等于「部分」——一个目录会横跨两卷，
        # 也有 math/number/ 这样的子目录，所以数文件用 rglob。
        by_dir = {}
        for ch in mapping["chapters"]:
            by_dir.setdefault(ch.split("/")[0], []).append(ch)
        # 表按**读者**的口径列：中文部分名、章数、配套例题数。
        # 原先列的是英文目录名与「正文 16 / 16」——那是维护者的一致性自检
        # （磁盘文件数 vs `_mapping` 章数），对读者是噪声，而且它恒等于 N / N，
        # 真不一致时也有四向差集在管。目录名保持英文同样是内部口径（那是 URL 的 slug）。
        titles = folder_titles()
        lines = ["| 部分 | 章数 | 配套例题 |", "| --- | --- | --- |"]
        tot_w = tot_a = tot_q = 0
        for folder, chs in by_dir.items():
            d = DOCS / folder
            w = len([p for p in d.rglob("*.md") if p.name != "index.md"]) if d.exists() else 0
            a = len(chs)
            q = sum(len(mapping["chapters"][c]) for c in chs)
            lines.append(f"| {titles.get(folder, folder)} | {a} | {q} |")
            tot_w += w
            tot_a += a
            tot_q += q
        lines += [f"| **合计** | **{tot_a}** | **{tot_q}** |", ""]
        if tot_w != tot_a:
            # 磁盘章文件数与 _mapping 对不上——不写进 README（那是给读者看的），
            # 但也不能悄悄咽下去（09 教训四：闸门只覆盖它看得见的东西）。
            print(f"  ⚠ 磁盘章文件 {tot_w} 份，_mapping 登记 {tot_a} 章，对不上")

        # **四套题单只有这一张表。** 原先 README 里有两张：上一节「题目来源」
        # 一张（来源 / 题单 / 题号段 / 判题模式），这一节又一张（题单 / 题数 / …）——
        # 同样四行、讲同一批题单，读者不知道该看哪一张。删掉一列不解决问题，
        # 两张表就是两处会各自漂的东西（09 教训七 / 二十六）。
        # 合成一张之后，「题目来源」那一节只剩散文，不再有表。
        #
        # 来源链接与题号段都从 `data/_sources.json` 取（`sites[].url` / `sets[].range`），
        # 不在 README 里手写——加一套题单只改注册表那一份。
        lines += ["| 来源 | 题单 | 题号段 | 判题模式 | 题数 | 已写题解 | 通过样例 |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        seen_site = set()
        for s in sets_:
            rows = by_set[s["key"]]
            site = sites[s["site"]]
            # 同一来源的多套题单只在第一行给链接，后面写「同上」——
            # 四行里三个一样的长链接，读者只会觉得吵
            if s["site"] in seen_site:
                cell = "同上"
            else:
                cell = f"[{site['fullName']}]({site['url']})"
                seen_site.add(s["site"])
            lines.append(f"| {cell} | {s['name']} | {s.get('range', '—')} | "
                         f"{MODE.get(s['mode'], s['mode'])} | {len(rows)} | "
                         f"{sum(r['has_sol'] for r in rows)} | "
                         f"{sum('✅' in r['status'] for r in rows)} |")
        lines.append(f"| **合计** | — | — | — | **{total}** | **{has_sol}** | **{done}** |")
        lines.append("")

        # 判题机实测与 PyPy3 登记也一并生成，否则每次重跑都会把手写的说明冲掉。
        # **站名不写死**：原先一律写「牛客判题机」，而 P-M③ 之后这个计数里有 100 道
        # 力扣题（P1③ 锁定复核实测）。多于一个站点时列出分站数。
        submit = SOL / "_submit_report.md"
        judged_nos = re.findall(r"^\|\s*([A-Z]+\d+)\s*\|[^|]*(?:通过|AC)",
                                submit.read_text(encoding="utf-8"), re.M) if submit.exists() else []
        judged = len(judged_nos)
        by_site: dict = {}
        for no in judged_nos:
            nm = sites.get(store.site_of(no), {}).get("name", "")
            if nm:
                by_site[nm] = by_site.get(nm, 0) + 1
        detail = "＋".join(f"{k} {v}" for k, v in sorted(by_site.items(), key=lambda x: -x[1]))
        tail = (f"，{judged} 题通过判题机实测" + (f"（{detail}）" if len(by_site) > 1 else "")) if judged else ""
        lines.append(f"题解：**{has_sol} / {total} 已写，{done} 题通过官方样例{tail}**")
        langs = store.submit_langs()
        pypy = sorted((k for k, v in langs.items() if v == "pypy3"), key=store.sort_key)
        if pypy:
            lines += ["",
                      f"> 其中 {len(pypy)} 题（{' / '.join(pypy)}）登记为 **PyPy3** 提交：",
                      "> 算法已是最优形态，纯粹是 CPython 的常数过不去。",
                      "> 提交语言登记在各题的 `meta.json`（`langs.py.submitLang`），"
                      "理由写在各题解的文档字符串里。"]
        # 「## 进度」之外还有几个散落在导语里的数（README 开头那句「全书 N 章」、
        # 三卷表的章数、支持项目那一段）。它们同样是「加一章就会变」的量（09 教训七），
        # 但塞在句子中间，没法整段重写——所以用一对注释标记框住，只换中间那一段。
        #
        # **标记里的空格是必须的。** 写成 `<!--N:chapters-->`（尖括号里没有空格）时，
        # 有些 markdown 格式化插件会把它当成自动链接 `<...>`，改写成
        # `[!--N:chapters--](!--N:chapters--)` —— 这一版真的被推上过线，
        # GitHub 仓库首页上明晃晃印着 `!--N:chapters--`。
        # 加了空格就不再是自动链接的候选。`check_decisions` 的 `readme_markers` 盯着这件事。
        #
        # 标记本身在 GitHub 上不显示，**但不能放进代码围栏**（围栏里注释会原样印出来），
        # 所以目录树那一处是直接不写数。
        def _sync(body: str, key: str, val) -> str:
            return re.sub(r"(<!--\s*N:%s\s*-->)[^<]*(<!--\s*/N\s*-->)" % key,
                          lambda m: m.group(1) + str(val) + m.group(2), body)

        t = _sync(t, "chapters", tot_a)
        t = _sync(t, "problems", total)
        for v, n in volume_counts().items():
            t = _sync(t, "vol" + v, n)

        # 「进度」是 README 第一大块（读者路径）的最后一节，块与块之间要有分隔线。
        # 那条 `---` **必须由这里吐出来**：它落在下面那个正则的替换区间里
        # （`[\s\S]*?` 懒到下一个 `
## ` 才停），手工写在正文里会被重跑一次就吃掉。
        lines.append("")
        lines.append("---")

        # 只吃「## 进度」这一节，遇到下一个二级标题就停手。
        # 原写法吃到文件尾，README 末尾新增的「仓库维护」小节在 P-M② 第 2 步
        # 被它整段冲掉过一次——脚本只该改自己那一节。
        t = re.sub(r"## 进度\n\n[\s\S]*?(?=\n## |\Z)",
                   "## 进度\n\n" + "\n".join(lines) + "\n", t)
        readme.write_text(t, encoding="utf-8")

    print(f"题目 {total}，已写题解 {has_sol}，通过 {done}")
    for s in sets_:
        print(f"  {sites[s['site']]['name']} · {s['name']:<16} {len(by_set[s['key']]):>4} 题")
    print(f"索引 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
