// 题解总览有 165 行，翻着找太慢。给标了 .q-table 的表格加一个即时筛选框：
// 按题号、标题、讲解章节任意片段过滤，回车不刷新页面。
//
// document$ 是 Material 提供的页面就绪流；navigation.instant 换页时会再次触发，
// 所以这里用 dataset 标记，避免同一张表挂两个筛选框。

function mountTableFilter(wrap) {
  if (wrap.dataset.filterMounted) return;
  const table = wrap.querySelector("table");
  if (!table) return;
  wrap.dataset.filterMounted = "1";

  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const bar = document.createElement("div");
  bar.className = "q-filter";

  const input = document.createElement("input");
  input.type = "search";
  input.className = "q-filter__input";
  input.placeholder = wrap.dataset.filterHint || "筛选：题号、标题或讲解章节";
  input.setAttribute("aria-label", input.placeholder);

  const count = document.createElement("span");
  count.className = "q-filter__count";

  const total = rows.length;
  const report = (n) => {
    count.textContent = n === total ? `${total} 题` : `${n} / ${total} 题`;
  };
  report(total);

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    let shown = 0;
    for (const row of rows) {
      const hit = !q || row.textContent.toLowerCase().includes(q);
      row.hidden = !hit;
      if (hit) shown += 1;
    }
    report(shown);
  });

  bar.append(input, count);
  // Material 会在运行时给表格套一层 .md-typeset__table，table 未必是 wrap 的直接子节点
  wrap.prepend(bar);
}

document$.subscribe(() => {
  document.querySelectorAll(".q-table").forEach(mountTableFilter);
});
