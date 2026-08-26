"""BM48 数据流中的中位数 —— 判题驱动器（不含解法）。

输入是一串数字，每读入一个就 Insert 一次、再取一次 GetMedian，
期望输出是各次中位数按 `%.2f` 格式、空格分隔拼成的**一个字符串**
（`[5,2,3]` -> `"5.00 3.50 3.00 "`，注意结尾那个空格）。
"""


def run(ns, input_text, codec):
    nums = codec.parse_value(input_text, codec.NOWCODER) or []
    if not isinstance(nums, list):
        nums = [nums]
    sol = ns["Solution"]()
    parts = []
    for n in nums:
        sol.Insert(n)
        parts.append("%.2f" % sol.GetMedian())
    return " ".join(parts) + " " if parts else ""
