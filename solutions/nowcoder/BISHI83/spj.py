"""BISHI83 迷宫问题 —— 路径类题目的校验器。

题目保证可行路径唯一，但输出的是「一条路径」而非唯一数值，
所以用 spj 真正按题目约束逐条验证，而不是和标准输出逐字符比对：

  1. 每行格式必须是 "(x,y)"（允许行内多余空白）；
  2. 路径非空，首格必须是 (0,0)，末格必须是 (h-1, w-1)；
  3. 每个坐标都在 [0,h) x [0,w) 内，且对应格子是空方格 '0'；
  4. 相邻两步必须是上下左右四联通（曼哈顿距离恰为 1）；
  5. 不允许重复经过同一个格子（保证是一条简单路径，不是原地打转刷步数）。
"""
import re

_CELL = re.compile(r"^\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)$")


def check(inp: str, out: str) -> bool:
    tok = inp.split()
    if len(tok) < 2:
        return False
    h, w = int(tok[0]), int(tok[1])
    g = tok[2:2 + h * w]
    if len(g) != h * w:
        return False

    lines = [ln.strip() for ln in out.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return False

    path = []
    for ln in lines:
        m = _CELL.match(ln)
        if not m:
            return False
        path.append((int(m.group(1)), int(m.group(2))))

    if path[0] != (0, 0) or path[-1] != (h - 1, w - 1):
        return False

    seen = set()
    prev = None
    for x, y in path:
        if not (0 <= x < h and 0 <= y < w):
            return False
        if g[x * w + y] != "0":          # 必须是空方格
            return False
        if (x, y) in seen:               # 不能重复经过
            return False
        seen.add((x, y))
        if prev is not None:
            if abs(prev[0] - x) + abs(prev[1] - y) != 1:   # 必须四联通相邻
                return False
        prev = (x, y)
    return True
