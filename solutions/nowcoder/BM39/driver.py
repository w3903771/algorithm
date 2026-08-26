"""BM39 序列化二叉树 —— 判题驱动器（不含解法）。

这题的两个方法必须咬合着用：Serialize 出来的串再喂给 Deserialize，
还原出的树跟原树一致才算对。序列化格式本身不限，所以不能比中间那个串，
只能比最终的树——判的是「一个来回不丢信息」。
"""


def run(ns, input_text, codec):
    root = codec.build_tree(codec.parse_value(input_text, codec.NOWCODER))
    sol = ns["Solution"]()
    return codec.dump_tree(sol.Deserialize(sol.Serialize(root)))
