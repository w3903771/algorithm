// arithmatex 的 generic 模式把 $...$ / $$...$$ 编译成 \(...\) / \[...\]，
// 再由 MathJax 渲染。这样 MathJax 不需要自己扫描 $ 符号，
// 正文里出现的美元号、shell 变量不会被误当成公式。
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    // 只处理 arithmatex 标记过的节点，正文其余部分一概跳过。
    // 右侧目录里的标题是纯文本（\(...\) 原样留着），一并放行，
    // 否则带公式的小标题在目录里会露出反斜杠。
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex|md-nav__link|md-ellipsis"
  }
};

// navigation.instant 换页时不会重新执行 MathJax 的启动流程，需要手动重排。
document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
