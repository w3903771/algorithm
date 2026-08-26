"""BM87 合并两个有序的数组 —— 判题驱动器（不含解法）。

签名是 `merge(A, m, B, n) -> void`，四个参数，但样例输入只有两段：
`[4,5,6],[1,2,3]`。m、n 不在输入里——牛客后台自己取 m=len(A)、n=len(B)，
并且**预先把 A 扩容到 m+n 长度**（后半段是待填的空位），题解才好从后往前原地填。

通用 harness 只会按签名喂参，四个形参配两个值就补两个 None，必然 RE；
就算不 RE，A 没扩容也没法原地合并。所以这题得自己驱动。

答案在**入参 A** 里（返回 void），所以驱动器返回 A。
"""


def run(ns, input_text, codec):
    parts = codec.parse_nowcoder(input_text)
    a = list(parts[0] or []) if parts else []
    b = list(parts[1] or []) if len(parts) > 1 else []
    m, n = len(a), len(b)
    a += [0] * n                     # 后台约定：A 已经扩容到 m + n
    ns["Solution"]().merge(a, m, b, n)
    return a
