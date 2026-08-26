"""LC236 二叉树的最近公共祖先 —— 判题驱动器（不含解法）。

两处口径不一致，都出在「metaData 描述的是判题输入格式，不是提交签名」：

1. metaData 把 p、q 声明成 integer（判题输入里给的确实是两个值），
   而官方 Python 模板是 `lowestCommonAncestor(self, root, p: 'TreeNode', q: 'TreeNode')`
   ——线上传进来的是两个**结点对象**。题解要按线上那份写才能提交，
   于是本地按 metaData 喂两个整数就对不上。这里按值在树里找到结点再传对象。

2. 返回类型声明是 TreeNode，通用编码器会把整棵子树摊成层序序列，
   而期望输出只是那个结点的**值**（`3` / `5` / `1`）。所以这里返回 val。

题面保证结点值互不相同，按值定位无歧义。
"""


def run(ns, input_text, codec):
    vals, pv, qv = codec.split_params(input_text, 3, codec.LEETCODE)
    root = codec.build_tree(vals)

    # 按值找结点对象：官方签名收的是结点，不是值
    found = {}
    stack = [root]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if n.val in (pv, qv):
            found[n.val] = n
        stack.append(n.left)
        stack.append(n.right)

    got = ns["Solution"]().lowestCommonAncestor(root, found.get(pv), found.get(qv))
    return None if got is None else got.val
