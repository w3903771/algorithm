"""把正文里指向题解的链接统一改成**站内题解页**。

站点在构建期为每道题生成一页 `solutions/<题号>/`（见 `hooks/build_pages.py`），
读者不必跳到 GitHub 看源码，所以正文里的三类旧写法都要收敛过来：

1. `https://github.com/.../blob/main/solutions/BISHIx.py` -> `../solutions/BISHIx.md`
2. `../../solutions/BISHIx.py`（站点上 404，`solutions/` 不在 docs/ 下）-> 同上
3. `../../sources/05-nowcoder/problems/BISHIx.md` -> 牛客原题链接
   （`sources/` 被 .gitignore 排除，文件根本不在仓库里）

链接深度按文件所在层级算，脚本是幂等的，可以反复运行。

用法: uv run python scripts/fix_solution_links.py [--dry]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"        # 公开数据：站点构建与 check_prose 要读，随仓库发布

BLOB = re.compile(
    r"\]\(https://github\.com/w3903771/algorithm/blob/main/solutions/"
    r"((?:BISHI|PIO)\d+)\.py\)"
)
REL = re.compile(r"\]\((?:\.\./)+solutions/((?:BISHI|PIO)\d+)\.py\)")
PROB = re.compile(r"\]\((?:\.\./)+sources/05-nowcoder/problems/((?:BISHI|PIO)\d+)\.md\)")


def problem_urls() -> dict:
    """题号 -> 牛客练习页 URL。优先用入库的 data/_problems.json。"""
    p = DATA / "_problems.json"
    if p.exists():
        return {no: it["url"] for no, it in json.loads(p.read_text(encoding="utf-8")).items()}
    out = {}
    for slug in ("bishi", "pio"):
        f = ROOT / "sources" / "05-nowcoder" / (slug + "_list.json")
        if f.exists():
            for it in json.loads(f.read_text(encoding="utf-8")):
                out[it["no"]] = it["url"]
    return out


def main(argv) -> int:
    dry = "--dry" in argv
    urls = problem_urls()
    if not urls:
        print("[警告] 未找到题目元信息，题面链接将跳过")
    total_files = total_links = 0
    for p in sorted(DOCS.rglob("*.md")):
        text = original = p.read_text(encoding="utf-8")
        # docs/ 下的深度决定要回退几层：`docs/ds/array.md` -> `../solutions/`、
        # `docs/math/number/basic.md` -> `../../solutions/`。
        # 章路径自 P-M① 起深度不固定，所以这里一直是算出来的，不是写死的。
        depth = len(p.relative_to(DOCS).parts) - 1
        prefix = "../" * depth if depth else ""

        def to_page(m):
            return f"]({prefix}solutions/{m.group(1)}.md)"

        text, n1 = BLOB.subn(to_page, text)
        text, n2 = REL.subn(to_page, text)
        n3 = 0
        if urls:
            def to_nowcoder(m):
                url = urls.get(m.group(1))
                return f"]({url})" if url else m.group(0)
            text, n3 = PROB.subn(to_nowcoder, text)

        n = n1 + n2 + n3
        if n and text != original:
            total_files += 1
            total_links += n
            print(f"{p.relative_to(ROOT)}: {n} 处")
            if not dry:
                p.write_text(text, encoding="utf-8")
    verb = "待改" if dry else "已改"
    print(f"{verb} {total_links} 处链接，涉及 {total_files} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
