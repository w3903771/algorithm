// 正文里的站外链接（原题链接、语言参考手册等）一律新开标签页。
//
// 理由是这类链接的用途是「对照着读」，不是「读完就走」：点原题链接的人
// 十有八九还要回到题解继续看。原地跳转会把当前页从历史里挤掉，回来要按后退，
// 而 navigation.instant 下的后退还得重新拉一次页面。
//
// 只处理 .md-content 里的链接——顶栏、侧栏、页脚的跳转属于站内导航，
// 那里的原地跳转是对的。判据是 host 不同，因此站内的相对链接、
// 页内锚点、mailto: 都不受影响。
//
// document$ 是 Material 提供的页面就绪流；navigation.instant 换页时会再次触发，
// 所以用 target 是否已设置来判断，避免重复处理。

function markExternalLinks(root) {
  for (const a of root.querySelectorAll("a[href]")) {
    if (a.target) continue;
    // 相对链接、锚点、mailto: 在这里会拿到当前页的 host 或空串，都不算站外
    let host;
    try {
      host = new URL(a.href, location.href).host;
    } catch (e) {
      continue;
    }
    if (!host || host === location.host) continue;
    a.target = "_blank";
    // noopener 断开新页面对 window.opener 的引用，顺带避免旧浏览器的性能问题
    a.rel = a.rel ? `${a.rel} noopener` : "noopener";
  }
}

document$.subscribe(() => {
  const content = document.querySelector(".md-content");
  if (content) markExternalLinks(content);
});
