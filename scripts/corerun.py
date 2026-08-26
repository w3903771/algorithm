"""核心代码模式的**执行驱动**：在子进程里加载题解、按签名喂参、把返回值编码出来。

单独一个文件而不是塞进 verify 里，是因为它必须跑在独立进程：
题解可能死循环、爆栈、`sys.exit()`，甚至污染 `sys.modules`——
这些都不该把判题机本身带走。verify 那边用 subprocess 调它，超时直接杀。

调用: python scripts/corerun.py <job.json>
job.json: {"solution": 路径, "func": 签名, "dialect": "leetcode"|"nowcoder",
           "input": 样例输入文本, "outParam": 原地修改题要读回的参数下标}
结果打到 stdout 的最后一行，带 `@@CORERUN@@ ` 前缀——
题解里常留 print 调试，不加前缀就会把输出搅乱。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codec  # noqa: E402

SENTINEL = "@@CORERUN@@ "


def make_namespace() -> dict:
    """题解运行的全局命名空间。

    两家站点的模板都**默认 ListNode / TreeNode 已经存在**（力扣写在注释里，
    牛客写在 Java 模板的注释里），Python 题解通常不会自己定义。
    所以这里预置好；题解若自己定义了，exec 时会覆盖掉这里的，互不干扰。
    typing 里的名字同理——力扣模板的签名带 `List[int]` 注解，不给就 NameError。
    """
    import bisect
    import collections
    import functools
    import heapq
    import itertools
    import math
    import re as _re
    import string
    from typing import (Any, Callable, Deque, Dict, Iterable, Iterator, List,
                        Optional, Sequence, Set, Tuple, Union)

    ns = {
        "__name__": "__solution__",
        "ListNode": codec.ListNode, "TreeNode": codec.TreeNode,
        "Interval": codec.Interval, "Point": codec.Point,
        # 力扣把带 random 指针的节点叫 Node，牛客叫 RandomListNode，两个名字都给
        "RandomListNode": codec.RandomListNode, "Node": codec.Node,
        "TreeLinkNode": codec.TreeLinkNode,
        "List": List, "Dict": Dict, "Set": Set, "Tuple": Tuple, "Optional": Optional,
        "Union": Union, "Any": Any, "Callable": Callable, "Iterable": Iterable,
        "Iterator": Iterator, "Sequence": Sequence, "Deque": Deque,
        "math": math, "collections": collections, "heapq": heapq, "bisect": bisect,
        "itertools": itertools, "functools": functools, "string": string, "re": _re,
    }
    return ns


def load_solution(path: Path) -> dict:
    ns = make_namespace()
    src = path.read_text(encoding="utf-8")
    exec(compile(src, str(path), "exec"), ns)
    return ns


def call_function(ns: dict, func: dict, args: list, out_param):
    """普通函数题：实例化 Solution，调声明的方法。

    返回 void 的题（力扣有 7 道，如 LC283 移动零、LC73 矩阵置零）答案留在**入参**里，
    调用完得回头读那个参数，读返回值只会拿到 None。
    """
    cls = ns.get(func.get("classname") or "Solution")
    if cls is None:
        raise RuntimeError("题解里没有 class Solution")
    obj = cls()
    name = func["name"]
    method = getattr(obj, name, None)
    if method is None:
        # 牛客与力扣偶尔大小写不一致（ReverseList / reverseList），宽松找一次
        for k in dir(obj):
            if k.lower() == name.lower() and not k.startswith("_"):
                method = getattr(obj, k)
                break
    if method is None:
        raise RuntimeError(f"题解里没有方法 {name}")
    ret = method(*args)
    if (func.get("return") or {}).get("type") == "void":
        idx = 0 if out_param is None else int(out_param)
        params = func.get("params") or []
        out_type = params[idx]["type"] if idx < len(params) else None
        return (args[idx] if idx < len(args) else None), out_type
    return ret, (func.get("return") or {}).get("type")


def call_design(ns: dict, func: dict, raw: list, dialect: str):
    """设计题：按操作序列驱动一串方法调用，逐个收返回值。

    两家的调用约定不一样，别混：
      力扣   ops[0] 是类名（构造），args[0] 是构造参数，输出首位固定是 null
             ["LRUCache","put","get"] / [[2],[1,1],[1]] -> [null,null,1]
      牛客   ops 里没有构造，构造参数跟在**输入末尾**，输出与 ops 一一对应
             ["set","get"],[[1,1],[1]],2 -> ["null","1"]
    """
    cls = ns.get(func.get("classname") or "Solution")
    if cls is None:
        raise RuntimeError(f"题解里没有 class {func.get('classname')}")
    ops = list(raw[0] or [])
    call_args = list(raw[1] or [])

    if dialect == codec.LEETCODE:
        ctor_args = list(call_args[0] or []) if call_args else []
        obj = cls(*ctor_args)
        out = [None]
        for op, a in zip(ops[1:], call_args[1:]):
            out.append(getattr(obj, op)(*(a or [])))
        return out

    obj = cls(*raw[2:])
    return [getattr(obj, op)(*(a or [])) for op, a in zip(ops, call_args)]


def load_driver(path: Path):
    """自定义驱动器：`run(ns, input_text, codec) -> 结果`。

    有些题的调用约定是题目语义的一部分，从签名里推不出来，比如
    牛客 BM42「用两个栈实现队列」的操作序列是 `["PSH1","PSH2","POP"]`——
    参数直接编在操作名里；BM39「序列化二叉树」要先 Serialize 再 Deserialize
    才能判等。这种一题一样的规矩不该塞进通用 harness，放到
    该题目录里的 driver.py（`solutions/<site>/<题号>/driver.py`），跟着题解一起入库。
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"driver_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "run", None)


def main(argv) -> int:
    job = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    func, dialect = job["func"], job["dialect"]
    ns = load_solution(Path(job["solution"]))

    driver_path = Path(job["driver"]) if job.get("driver") else None
    # 自定义驱动器与设计题自己决定输出形状，没有单一的「声明返回类型」可用
    out_type = None
    if driver_path and driver_path.exists():
        run = load_driver(driver_path)
        if run is None:
            raise RuntimeError(f"{driver_path.name} 里没有 run(ns, input_text, codec)")
        result = run(ns, job["input"], codec)
    elif func.get("kind") == "multi":
        raise RuntimeError(
            f"这题要实现多个方法（{'、'.join(m['name'] for m in func.get('methods') or [])}），"
            f"调用顺序推不出来，需要该题目录里的 driver.py")
    elif func.get("kind") == "design":
        raw = codec.split_params(job["input"], 0, dialect)
        result = call_design(ns, func, raw, dialect)
    else:
        args = codec.to_args(job["input"], func.get("params") or [], dialect)
        result, out_type = call_function(ns, func, args, job.get("outParam"))

    sys.stdout.write("\n" + SENTINEL
                     + json.dumps(codec.encode(result, out_type),
                                  ensure_ascii=False, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
