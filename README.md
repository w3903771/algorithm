# Python 语法 + 算法教程大全

用 Python 打算法笔试/竞赛的完整教程。语法部分覆盖菜鸟教程 Python3 全部算法相关内容，
算法部分覆盖三处本地资料（C++ 算法代码库、信息学竞赛课件、NOIP 模板文档）的全部知识点，
每章配套牛客真题与**经过验证**的 Python 题解。

## 快速导航

| 入口 | 说明 |
| --- | --- |
| [知识大纲](docs/00-知识大纲.md) | 十部分 74 章的完整骨架，含来源与例题标注 |
| [大纲审计报告](docs/00-大纲审计报告.md) | 题目归属、章节例题、需求覆盖的自动校验结果 |
| [来源覆盖审计](docs/00-来源覆盖审计.md) | S2/S3/S4 三处资料 169 个知识点的承接情况 |
| [题解验证报告](solutions/_verify_report.md) | 各题跑官方样例的通过情况 |

## 目录结构

```
docs/            教程正文（十部分 74 章）
solutions/       牛客 165 题的 Python 题解，_spj/ 下是特判校验器
scripts/         抓取、提取、验证、提交脚本
sources/         从五处来源提取的原始资料
  01-cpp-algo-ds/       C++ 算法与数据结构代码
  02-oi-courseware/     信息学竞赛课件 day1–day10
  03-pascal-template/   NOIP 模板文档
  04-runoob/            菜鸟教程 Python3（算法相关部分）
  05-nowcoder/          牛客 165 题的题面与题单
```

## 环境

Python 3.9 + uv：

```bash
uv sync
```

## 常用命令

```bash
# 验证题解（跑官方样例）
uv run python scripts/verify.py            # 全部
uv run python scripts/verify.py PIO        # 只跑 PIO 开头的
uv run python scripts/verify.py BISHI136

# 审计大纲与来源覆盖
uv run python scripts/audit_outline.py
uv run python scripts/audit_sources.py

# 提交到牛客判题机（需先登录一次）
uv run python scripts/nc_login.py          # 打开浏览器手动登录，保存会话
uv run python scripts/nc_submit.py --langs # 先查各题支持哪些语言
uv run python scripts/nc_submit.py PIO     # 提交

# 重新抓取来源（HTTP 有缓存，重跑很快）
uv run python scripts/extract_local.py     # 本地 C++/课件/Pascal 资料
uv run python scripts/extract_legacy.py    # rar 里的 .doc/.ppt（需 Office）
uv run python scripts/runoob_fetch.py      # 菜鸟教程
uv run python scripts/runoob_prune.py      # 剔除与算法竞赛无关的页面
uv run python scripts/nc_fetch_list.py     # 牛客题单
uv run python scripts/nc_fetch_detail.py   # 牛客题面
```

## 题目来源

牛客在线编程 <https://www.nowcoder.com/exam/oj?questionJobId=10&subTabName=online_coding_page>

- **笔试模板必刷** BISHI1–BISHI147（147 题）
- **输入输出练习** PIO1–PIO18（18 题）

## 进度

| 部分 | 章数 | 正文 | 题解 |
| --- | --- | --- | --- |
| part1 Python 基础 | 16 | 3 / 16 | — |
| part2 竞赛基本功 | 5 | 1 / 5 | 18 / 22 |
| part3 数据结构 | 10 | 0 / 10 | 0 |
| part4 基础算法 | 11 | 0 / 11 | 0 |
| part5 搜索 | 3 | 0 / 3 | 0 |
| part6 字符串 | 4 | 0 / 4 | 0 |
| part7 数学 | 6 | 0 / 6 | 0 |
| part8 图与树 | 5 | 0 / 5 | 0 |
| part9 动态规划 | 5 | 0 / 5 | 0 |
| part10 进阶专题 | 9 | 0 / 9 | 0 |
| **合计** | **74** | **4 / 74** | **18 / 165** |
