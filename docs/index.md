---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<img class="hero__logo" src="assets/logo.png" alt="" width="88" height="88">

<p class="hero__eyebrow">Python · 笔试与竞赛</p>

# 算法笔记 { .hero__title }

<p class="hero__lede">
从 <code>print("Hello")</code> 一路写到树链剖分。<!-- N:chapters --> 章正文按顺序读就是一条完整的路，
配套 <!-- N:problems --> 道真题在站内直接看思路和完整源码，不用跳出去翻仓库。
</p>

<ul class="hero__stats">
  <li><span class="hero__num"><!-- N:chapters --></span><span class="hero__label">章正文</span></li>
  <li><span class="hero__num"><!-- N:problems --></span><span class="hero__label">道真题</span></li>
  <li><span class="hero__num hero__num--ac"><!-- N:judged --></span><span class="hero__label">题通过判题机</span></li>
</ul>

[从头开始读](python/syntax.md){ .md-button .md-button--primary }
[直接看题解](solutions/index.md){ .md-button }

</div>

## 和别的算法教程不一样在哪

<div class="proof" markdown>

<div class="proof__card" markdown>
<span class="proof__tag">题解</span>
### 每一份都真的提交过

<!-- N:judged --> 道题在**官方判题机上拿到过真实判定**，不是「思路应该没问题」。
过不去的会写清为什么——包括那几道 CPython 常数过不去、只能换 PyPy3 的。
</div>

<div class="proof__card" markdown>
<span class="proof__tag">正文</span>
### 印出来的代码本身能跑

正文里的代码块不是示意。它们被单独抽出来喂官方样例跑过，
**跑不过的不许印在正文里**，抄下来就能用。
</div>

<div class="proof__card" markdown>
<span class="proof__tag">路线</span>
### 一条主线，不跳步

<!-- N:chapters --> 章按依赖顺序排好，每章开头写清前置。
不是知识点的堆叠，是从语法到省选难度的**一条连续的路**。
</div>

</div>

## 怎么读

<div class="readpath" markdown>

<div class="readpath__card" markdown>
<span class="readpath__no">01</span>
### 零基础，想系统过一遍

从 **卷一** 顺序读到 **卷三**，每章末尾的例题当场做掉。
章节底部有「上一章 / 下一章」，一路点下去就行。

[从第一章开始](python/syntax.md){ .md-button .md-button--primary }
</div>

<div class="readpath__card" markdown>
<span class="readpath__no">02</span>
### 只想补某个知识点

在下面的章节盘里找，或者用右上角搜索。
每章开头的引言写清了它依赖哪几章。

[跳到章节盘](#全书章节){ .md-button }
</div>

<div class="readpath__card" markdown>
<span class="readpath__no">03</span>
### 在刷题，卡在某道题上

按题号找题解。每页都写了「这题考什么、数据规模、坑在哪」，
再往下是能直接跑的完整代码。

[按题号查](solutions/index.md){ .md-button }
</div>

</div>

## 三卷分别是什么

<div class="volumes" markdown>

<div class="volume" markdown>
<div class="volume__num"><span class="volume__n"><!-- N:vol1 --></span><span class="volume__k">章</span></div>

**卷一 · 核心卷**　Python 语法、竞赛基本功、数据结构与基础算法。
**笔试面试要用的东西基本都在这一卷**，读完就能开始刷题。
</div>

<div class="volume" markdown>
<div class="volume__num"><span class="volume__n"><!-- N:vol2 --></span><span class="volume__k">章</span></div>

**卷二 · 提高卷**　图论、动态规划、数学与字符串算法。
开始出现「知道名字也未必写得对」的东西，模板与坑点都写在正文里。
</div>

<div class="volume" markdown>
<div class="volume__num"><span class="volume__n"><!-- N:vol3 --></span><span class="volume__k">章</span></div>

**卷三 · 竞赛卷**　平衡树、树链剖分、CDQ 分治、整体二分这一类。
省选难度，正文默认前两卷已经读完。
</div>

</div>

!!! tip "关于 Python 的常数"

    正文默认用 CPython 的写法。少数几道题 CPython 物理上过不去，题解页会标出 `pypy3`，
    原因写在那一页的「为什么必须 PyPy3」里。

## 全书章节

章号就是全书的地图：`01–16` 是语法，`20–24` 是竞赛基本功，`30` 往后按数据结构、算法、专题递增。
右侧的数字是这一章配了几道真题。

<!-- CHAPTER-MAP -->

## 题解与速查

- [**题解总览**](solutions/index.md) —— <!-- N:problems --> 道题一张表，可按题号、难度、讲解章节对照着找。
- [**附录 A · 题单总索引**](appendix/a-problems.md) —— 四套题单按来源分节，题号、难度、官方标签、讲解章节的完整对照，也支持按章节反查例题。
- [**附录 B · Python 算法模板速查**](appendix/b2-python-templates.md) —— 考场上直接抄的模板。
- [**附录 C · Python 竞赛避坑清单**](appendix/c-pitfalls.md) —— 递归深度、输入输出、浮点、整数除法这些老坑的一页纸清单。
