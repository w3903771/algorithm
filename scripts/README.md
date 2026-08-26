# scripts/ 说明

本目录不随站点发布，但**已入库**（P0a 决议 Q1：脚本是交付物，`check_prose.py` 还要进 CI）。
它是**生成与校验教程内容的工具链**。
所有脚本都用 uv 运行，工作目录为项目根：

```bash
uv run python scripts/<脚本>.py
```

---

## 〇、命令速查

根 README 原先平铺着二十几条命令，其中大半**外人一条也跑不了**（缺登录会话、
缺原始资料、缺 Office）。那份文档现在只留「本地跑起来」与「怎么改」，
命令全收在这里，按**跑不跑得起来**分组。

### 0.1 clone 下来就能跑

```bash
uv sync                                     # 装依赖（Python 3.9+ 与 uv）

# 本地预览站点：题解页在构建期生成，不入库
uv run mkdocs serve                         # http://127.0.0.1:8000
uv run mkdocs build                         # 静态产物到 site/

# 验证题解跑官方样例。ACM 与核心代码两种判题模式按题单自动分派
uv run python scripts/verify.py             # 全部 366 道
uv run python scripts/verify.py PIO         # 只跑 PIO 开头的
uv run python scripts/verify.py BISHI136    # 单独一道
uv run python scripts/test_corejudge.py     # 核心代码判题链路自测

# 验证**正文里印出来的代码**（与题解是两份东西）
uv run python scripts/verify_docs.py

# CI 跑的就是这两条
uv run python scripts/check_syntax.py       # 全库源码的 3.9 语法闸门
uv run python scripts/check_prose.py        # 文风与结构校验

# 站内链接与锚点
uv run python scripts/check_links.py
uv run python scripts/check_links.py --fix   # 自动改正能改的那些
```

### 0.2 要额外输入才跑得起来

| 命令 | 缺什么就跑不了 |
| --- | --- |
| `gen_index.py` | **`sources/` 的题单 JSON**。题面与抓取产物不入库（体量与版权），`data/_problems.json` 是它们的发布快照——站点构建读快照，不需要重新生成 |
| `audit_topics.py` · `audit_depth.py` · `audit_sources.py` · `check_decisions.py` | **`dev/data/` 的 `_topics` / `_source_topics` / `_decisions`**。这三份是开发侧数据，不随仓库发布 |
| `check_orphan.py` · `audit_outline.py` · `audit_newsets.py` · `check_templates.py` | 能跑，但报告写进 `dev/audit/`，该目录不随仓库发布——首次跑会自己建 |
| `nc_*.py` · `lc_*.py` | **`.auth/` 里的登录会话**。先跑一次 `nc_login.py` / `lc_login.py` 手动登录 |
| `extract_local.py` · `extract_legacy.py` · `runoob_*.py` | **本地原始资料**（C++ 代码库、竞赛课件、rar 里的 .doc/.ppt），`extract_legacy` 还要装 Office |
| `migrate.py` · `migrate_solutions.py` · `diff_build.py` | 一次性迁移工具，已经跑完；留着是为了留痕与复算 |

### 0.3 维护者日常

```bash
# 写一道核心代码题之前，先生成带正确签名的骨架
uv run python scripts/new_solution.py LC1

# 提交到判题机（先登录一次；判题机提交很慢，别混在写作里跑）
uv run python scripts/nc_login.py           # 打开浏览器手动登录，保存会话
uv run python scripts/nc_submit.py --langs  # 先查各题支持哪些语言
uv run python scripts/nc_submit.py PIO
uv run python scripts/lc_login.py           # 力扣走持久化 profile
uv run python scripts/lc_submit.py --check  # 确认会话真能提交
uv run python scripts/lc_submit.py --dry LC1
uv run python scripts/lc_submit.py LC
uv run python scripts/lc_submit.py --keep-comments LC1   # 默认剥注释，这样保留

# 重新抓取来源（HTTP 有缓存，重跑很快）
uv run python scripts/extract_local.py      # 本地 C++/课件/Pascal 资料
uv run python scripts/extract_legacy.py     # rar 里的 .doc/.ppt（需 Office）
uv run python scripts/runoob_fetch.py
uv run python scripts/runoob_prune.py       # 剔除与算法竞赛无关的页面
uv run python scripts/nc_fetch_list.py      # 牛客题单（BISHI / PIO / BM）
uv run python scripts/nc_fetch_detail.py    # 牛客题面
uv run python scripts/nc_fetch_template.py  # 牛客核心代码题的函数签名
uv run python scripts/lc_fetch.py           # 力扣热题 100 题单 + 题面

# 重建生成物
uv run python scripts/gen_index.py          # 附录 A、README 进度表、data/_problems.json
uv run python scripts/check_prose.py --sync # 00 号文件 §D4 / §D8 两张数字表
```

> **提交语言**由各题 `meta.json` 的 `langs.py.submitLang` 覆盖，默认 Python3。
> 目前 5 题登记为 `pypy3`（BISHI103 / 128 / 130 / 138 / 147）。

---

## 一、内容生成

| 脚本 | 作用 | 何时重跑 |
| --- | --- | --- |
| `extract_local.py` | 把 S2/S3/S4 三处本地资料（C++ 代码、竞赛课件、Pascal 模板）抽成 Markdown 到 `sources/01~03` | 源资料变动时 |
| `extract_legacy.py` | 处理 rar 里的老格式 `.doc`/`.ppt`（走 Office COM），产出《背包九讲》等 | 同上，需装 Office |
| `runoob_fetch.py` | 抓菜鸟教程 Python3 全部页面到 `sources/04-runoob` | 需要更新语法资料时 |
| `runoob_prune.py` | 剔除与算法竞赛无关的页面（84 → 45 页） | 紧跟 `runoob_fetch.py` |
| `nc_fetch_list.py` | 抓牛客三套题单（BISHI 147 + PIO 18 + BM 101）到 `sources/05-nowcoder`；加题单只改 `TOPICS` | 题单变动时 |
| `nc_fetch_detail.py` | 抓牛客 266 道题的题面（描述 / 输入输出 / 样例）| 改了 `nc_html2md.py` 后必须重跑 |
| `lc_fetch.py` | 抓力扣热题 100 的题单、题面、函数签名与样例到 `sources/06-leetcode` | 题单变动时 |
| `nc_fetch_template.py` | 抓牛客核心代码题的**函数签名**（开浏览器读编辑器状态，Java 模板里解析）与官方样例；`--reparse` 可离线重解析 | 加了核心代码题单、或改了签名解析正则 |
| `gen_index.py` | 由映射与验证结果生成附录 A、README 进度表与 `docs/_problems.json`（站点构建期要用） | 题解或章节变动后 |
| `audit_newsets.py` | 新题单覆盖盘点：难度分布、BM/LC 重题、章节对接、判题缺口 | 加了题单后 |
| `new_solution.py` | 按签名生成题解骨架到 `solutions/<site>/<题号>/`（`sol.py` ＋ `meta.json`，只有签名与元信息，**不含解法**） | 开写每道核心代码题之前 |
| `lc_login.py` | 打开浏览器手动登录力扣，会话存进**持久化配置** `.auth/leetcode_profile/`；`--check` 只查状态 | 首次提交力扣前 |
| `lc_submit.py` | 把 `solutions/leetcode/` 下的题解提交到力扣判题机，拿真实判定 | 写完力扣题解后 |
| `fix_solution_links.py` | 把正文里的题解链接统一改成站内题解页 `../solutions/<题号>.md` | 新增题解引用后 |

`nc_common.py`（会话、限速、HTTP 缓存）与 `nc_html2md.py`（题面 HTML → Markdown）、
`lc_common.py`（力扣 GraphQL 会话、限速、缓存、HTML → Markdown）、
`codec.py`（核心代码模式的序列化编解码）、`corerun.py`（在子进程里按签名调题解）、
`submit_report.py`（两个提交脚本共用的结果存取与报告渲染）、
**`sol_store.py`（题号 → 站点 → 题目录的查表层，外加 `meta.json` 读写）**
是被上面几个脚本共用的库，不单独执行。

> **`sol_store.py` 是「题解在哪」的唯一权威**。`solutions/` 自 P-M③ 起按站点分层
> （`solutions/<site>/<题号>/`），9 个消费方一律从它取路径，谁都别再自己拼——
> 接洛谷时只改 `data/_sources.json` 的 `prefix → site` 一处。

自测：`test_html2md.py`（题面 HTML 转换）、`test_corejudge.py`（核心代码判题全链路，
拿真实题面 + 临时夹具跑，不往 `solutions/` 落任何文件）。

**题单注册表在 `data/_sources.json`**（P-M② 从 `docs/` 归位到 `dev/data/`；**P-S① 又搬到根 `data/`**——它是站点构建的输入，必须随公开仓发布）。
新增一套题单：写抓取脚本产出同构的 `<key>_list.json` / `raw/*.json`，然后在注册表里加一条，
`gen_index.py` / `audit_outline.py` / `hooks/build_pages.py` / `sol_store.py` 都会自动跟上。

> 站点侧还有一份构建期代码：仓库根目录的 `hooks/build_pages.py`。
> 它在 `mkdocs build` 时把各题的 `sol.py` 渲染成站内题解页、生成题解总览、
> 把首页与部分索引页里的 `<!-- CHAPTER-MAP -->` 换成章节盘。
> 它放在 `hooks/` 是 `mkdocs.yml` 的 `hooks:` 配置要求，与 `scripts/` 入不入库无关；
> CI 是完整 checkout，构建期 `import sol_store` 拿得到。

## 二、校验（十二道闸门）

| 脚本 | 校验什么 | 通过标准 |
| --- | --- | --- |
| `verify.py` | `solutions/` 下的题解跑官方样例 | 366 / 366 |
| `verify_docs.py` | **正文里印的代码**跑官方样例（与题解是两份东西） | 201 / 201 |
| `check_links.py` | 站内相对链接与 `#锚点`；`--fix` 可自动改正 | 0 断链 |
| `check_problems.py` | 抓下来的题面有无公式截断、缺样例 | 0 截断 |
| `test_html2md.py` | 题面解析器的回归测试（11 例全部来自真实踩坑） | 11 / 11 |
| `audit_outline.py` | 165 题是否都有章节归属、89 章是否都有例题、48 条需求是否都有承接 | 需求 0 无承接；「无例题 8 章」与「未分配 201 题」是已登记的待办（P1②/P4/P5） |
| `audit_sources.py` | S2/S3/S4 的 169 个知识点是否都被章节承接 | 全绿 |
| `check_syntax.py` | 全库 `.py` 用**运行它的解释器**做 `ast.parse`——「全书代码兼容 Python 3.9」这句承诺的执行者。不用 `compileall`：那会往每个题目录撒 `__pycache__`，而 `solutions/**` 被 gitignore 盖着，看不见 | 440 / 440 |
| `check_prose.py` | 文风规范（`dev/spec/正文文风规范.md`）的可执行版 ＋ 结构体检；**只用标准库、进 CI**；生成 00 号文件 §D4 / §D8 两张数字表 | 超出 `data/_prose_baseline.json` 的棘轮基线即失败 |
| `check_orphan.py` | 全 366 题逐题查正文引用，按 `meta.topics` 分三档（挂章零引用 · 只在章首例题行 · 尚未归属） | 甲 0、题号不存在 0；「丙 201」是已登记待办（Q7 / P1②） |
| `audit_depth.py` | 章的深度分档 ＋ 知识点三层覆盖（L1 认领 / L2 讲透 / L3 有题），anchors 支持同义词数组 | L1/L2 无新问题；「L2 未登记 anchors 164」是 P1 的工作面 |
| `audit_topics.py` | 整条链的贯通性：知识点 → 章存在 → 章有例题 → 例题被正文引用 → 例题有判定，报「断在第几环」 | 「章存在」与「例题被正文引用」两环为 0；「章有例题 8」是 Q7 的已知待办 |
| `check_templates.py` | **盘点**正文里未验证的代码段，按模板类型与章分类、找跨章重复，为 P2 的抽取列清单 | 不设阈值，产出清单不当闸门 |
| `check_decisions.py` | 决议表逐条断言（断言表 `dev/data/_decisions.json`，正本 `dev/notes/拆分点.md`） | 41 / 41，映射缺口 0 |

两个 `verify*.py` 都是**累积式**的（结果落 `_verify_state.json`），
按题号过滤运行不会覆盖其它批次的结论——这是多进程并行写作时踩过的坑。
**状态文件一律以题号（`verify_docs` 是 `docs/` 相对路径）为键，不用文件名**：
文件名会随重组变，键跟着变就会留下一堆永远不失效的旧条目（09 号文件 教训六）。

`check_links.py` 的锚点**以 `mkdocs build` 的产物为准**，不自己重算 slug：
pymdownx 的 slugify 直接调用与经 toc 扩展调用对全角空格的处理不一致（前者丢弃、后者转成分隔符），
自己重算会漏报。

## 三、维护

| 脚本 | 作用 |
| --- | --- |
| `fix_solution_links.py` | 把指向 `solutions/`、`sources/` 的相对链接改成绝对链接（幂等，可反复跑） |
| `migrate_solutions.py` | P-M③ 的 `solutions/` 重组工具。`--dry` 预览、无参落盘、`--sync` 重刷 `meta.json` 的派生字段（`site` `set` `mode` `title` `url` `topics`）。**改完 `_mapping.json` 的章节归属后要跑一次 `--sync`** |
| `nc_login.py` | 打开浏览器手动登录牛客一次，会话存到 `.auth/`（该目录已 gitignore） |
| `nc_submit.py` | 带登录态提交题解并轮询判题结果；`--langs` 只查语言不提交，`--retry` 重提上轮失败的题 |
| `nc_solutions.py` | 抓某题的**社区题解**全文到 `sources/05-nowcoder/community/`，卡住时用来看别人的思路 |

`nc_submit.py` 的提交语言由各题 `meta.json` 的 `langs.py.submitLang` 覆盖，默认 Python3。
目前有 5 题登记为 `pypy3`（BISHI103 / 128 / 130 / 138 / 147）——
它们的算法已经是最优形态，纯粹是 CPython 的常数过不去，理由写在各自题解的文档字符串里。

`nc_solutions.py` **不做语言筛选**：站上大部分题解没打语言标签，
按 Python3 过滤会得到「现在还没有解题哦」，把真正有用的题解全滤掉。

---

## 附：牛客站点的逆向结论

以下结论由一批一次性探针脚本得出，探针已删除，结论固化在此，避免重复劳动。

> **2026-08 站点改版**：判题机换了域名、提交接口加了签名 token、语言标识从字符串
> 变成数字 id、题目页 URL 必须带查询参数。下面已是改版后的结论，
> 旧写法（`/api/service/judge/submit` 打在 www、`language: "python3"`）现在全部失效。

### 页面结构

| 页面 | 性质 |
| --- | --- |
| `/exam/oj?questionJobId=10` | 题库首页，SSR 可用；脚本拿它当**同源发请求的落脚页** |
| `/exam/oj/ta?tpId=<N>` | SSR，`window.__INITIAL_STATE__` 里有题单结构 |
| `/practice/<uuid>` | **裸 uuid 现在返回 405** |
| `/practice/<uuid>?tpId=&tqId=&sourceUrl=` | 正常题目页，`window.pageInfo`、Monaco 编辑器都在这里 |
| `/questionTerminal/<uuid>` | **已废弃，返回 405**（原先抓题面用的就是它） |

`tqId` 传的是 `questionId`（不是题单里那个 `tqId` 字段），`sourceUrl` 是 URL 编码的返回地址。

### 接口

```
GET  /api/questiontraining/coding/getQuestionTopic?questionJobId=10   题单目录（免登录）
GET  /api/questiontraining/coding/getTopicQuestion?topicId=&page=&pageSize=   题目列表（免登录，pageSize ≤ 50）
GET  gw-c.nowcoder.com/api/sparta/base-oauth/access-token?token=&sceneType=1  取判题 token（需登录）
POST victorinox.nowcoder.com/api/service/judge/submit                 提交（需登录 + token）
GET  victorinox.nowcoder.com/api/service/judge/submit-status          轮询判题结果（同上）
GET  /test/code/lanuage?questionId=                                   **已废弃，恒返回 data: []**
```

题单 `topicId`：**389 = 笔试模板必刷（BISHI1–147）**、372 = 输入输出练习（PIO1–18）、
295 = 面试必刷 TOP101、37 = 华为机试、13 = 剑指 offer。

判题机在 `victorinox.nowcoder.com`，与站点跨域，但对 `www.nowcoder.com` 开了 CORS，
所以在题库页里带 `credentials: 'include'` 直接 fetch 即可，不必去模拟点击。

提交体与轮询参数：

```jsonc
// POST /api/service/judge/submit?_=<毫秒时间戳>
{"content": "<源码>", "questionId": "11211624", "language": "11",
 "tagId": 0, "appId": 5, "userId": 163162568,
 "submitType": 1, "remark": "{}", "token": "<accessToken>"}
// -> {"code":0,"data":{"id":<submissionId>}}

// GET /api/service/judge/submit-status?id=&tagId=0&appId=5&userId=&submitType=1&remark={}&token=
// -> data: {status, desc, allCaseNum, caseIndex, input, expectedOutput, output, ...}
```

`data.status` 里 **0/1 是排队与判题中，5 是通过**，其余为各类失败；
`desc` 是给人看的判定文案（通过时为「恭喜！您提交的程序通过了所有的测试用例」）。

### 三个必须知道的坑

**1. token 是按用户签发的，不是按题目。** `accessToken` 解开是
`{"TLS.identifier": "<userId>", "TLS.sig": ..., "TLS.expire": 604800}`——
zlib + base64（`*`→`+`、`_`→`/`）。有效期 7 天，整轮提交共用一个即可，
`nc_submit.py` 把它缓存在 `.auth/judge_token.json`。
少了它提交会被判无权限，而不是报错，很难定位。

**2. `window.supportLang` 完全不可信。** 它恒为 `java,cpp`——
连公认支持 Python3 的 BISHI1 也是这个值，登录后也不变。
真实语言表在 **`window.__ncMonacoEditorApi.editorParams.questionInfo.supportLanguages`**
（形如 `{langId: 11, langName: "Python 3"}`），要等 Monaco 初始化完才有。
原先那个 `/test/code/lanuage` 接口现在恒返回空数组，别再用了。

**3. 语言用数字 id，且 `5` 是 Python 2。** 枚举为：

```
1 C   2 C++   3 Pascal   4 Java   5 Python(2)   8 Php   9 C#   10 Object C
11 Python 3   13 Javascript   16 R   17 Go   19 Ruby   20 Swift   21 Matlab
24 Pypy2   25 Pypy3   27 Rust   28~31 Kotlin/Scala/TypeScript/Groovy 等
```

提交必须精确用 `11`，**绝不能拿 `5` 当兜底**——那会以 Py2 语法判题，
`print()`、整数除法全线出错且难以定位。`nc_submit.py` 已按此处理，
并提供 `--pypy` 开关（走 `25`，语法兼容 Py3，速度快一个数量级）。

### 题面解析的两个历史 bug

修在 `nc_html2md.py`，回归用例在 `test_html2md.py`：

1. **公式从 `alt` 属性取会被引号截断**。题面里的 `\texttt{"Yes"}` 含双引号，
   会让 HTML 属性提前结束（BISHI55 的 Yes/No 因此整个丢失）。
   改从 `src` 的 `tex=` 查询参数取，URL 编码不受引号影响。
2. **排版占位判断误用前缀匹配**。`\quad 2 \cdot \sum ...` 这类以间距宏起头的**真公式**
   被整条当成占位符丢弃，影响 86 / 165 份题面，其中 BISHI84 的全部操作规则、
   BISHI96 的左右孩子定义、BISHI40 的两条核心约束等关键内容整段消失。
   现在只有「剥掉全部间距宏后什么都不剩」才判为占位。


## 力扣站点的逆向结论

抓题面匿名即可，走 `leetcode.cn/graphql/`；**提交**要登录，且比牛客难伺候。

```
POST leetcode.cn/graphql/                          题单、题面、metaData（匿名可读）
POST leetcode.cn/problems/<slug>/submit/           提交（需登录 + x-csrftoken 头）
GET  leetcode.cn/submissions/detail/<id>/check/    轮询判定（同上）
GET  leetcode.cn/api/progress/all/                 只用来探鉴权是否真的有效
```

提交体是 `{"lang":"python3","question_id":"<内部id>","typed_code":"<代码>"}`。
**`question_id` 是内部 id，不是题号**：LC1 两者恰好都是 1，但绝大多数题不一样，
所以抓题面时就把 `meta.internalId` 记了下来。

两个踩过的坑：

1. **会话与浏览器指纹绑定。** 像牛客那样「headed 登录导出 storage_state ->
   headless 新上下文导入」，GraphQL 读接口能过（`userStatus.isSignedIn` 为真），
   但提交 POST 一律 403 `User is not authenticated`，**而且那次失败之后整个会话
   被服务端作废**，连读接口都变成未登录。改用
   `launch_persistent_context(.auth/leetcode_profile)`，登录与提交跑同一个
   profile、同一套指纹，问题消失。牛客没有这套处置，`nc_submit` 照旧用 storage_state。

2. **`userStatus.isSignedIn` 不足以判断能不能提交。** 上面那个坏状态里它照样是
   真。提交接口走 DRF 鉴权，所以登录后要再探一个同样需要鉴权的 REST 接口
   （`/api/progress/all/` 返回 200 才算数），`lc_login --check` 与
   `lc_submit --check` 查的都是这个。
