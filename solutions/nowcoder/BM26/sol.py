# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/04a5560e43e24e9db4595865dc9c63a3
# 判题: 核心代码模式
# 签名: levelOrder(root: TreeNode) -> list<list<integer>>

"""BM26 求二叉树的层序遍历 —— BFS 按层扩展，每轮整层出队再整层入队。

这题考什么：
    层序遍历本身就是一次 BFS（广度优先搜索），难点不在遍历而在**分组**：
    题目要的不是一串扁平序列，而是每层一个子数组，所以必须随时知道
    「当前这一层到哪儿结束」。

    常见做法是把节点塞进一个队列，每轮先记下 len(queue) 再循环那么多次。
    这里换成更直白的「整层推进」：用一个列表 cur 恰好装住当前层的全部节点，
      1. 把 cur 里每个节点的值收成一行，追加进答案；
      2. 按从左到右的顺序把它们的非空孩子收集成下一层 nxt；
      3. cur = nxt，进入下一层，直到某层为空。
    每一轮的 cur 就是完整的一层，既不用分层标记也不用记长度。

        示例 2 的 {1,2,3,4,#,#,5}：
            cur = [1]        -> 行 [1]      孩子 -> [2, 3]
            cur = [2, 3]     -> 行 [2, 3]   孩子 -> [4, 5]（2 只有左孩子 4，3 只有右孩子 5）
            cur = [4, 5]     -> 行 [4, 5]   孩子 -> []
        结果 [[1],[2,3],[4,5]]，与样例输出一致。

    BFS 的框架与队列选型见 docs/search/bfs.md。

数据规模与复杂度：
    0 <= n <= 1500；时限「其他语言 2 秒」。
    每个节点被收集一次、被展开一次，时间 O(n)；
    空间 O(w)，w 是最宽一层的节点数，完全二叉树时约 n/2。

坑在哪：
  1. cur 是「整层重建」而不是当队列用。真把 list 当队列、逐个 pop(0)，
     每次都要把剩下的元素整体前移，n 个节点就是 O(n^2)；需要单端弹出时
     必须换 collections.deque。这里根本不弹出，所以 list 反而最合适。
  2. 下一层必须按「先左后右」收集。收集顺序就是这一行的输出顺序，
     反过来收会让每行都左右颠倒。
  3. 不要把 None 孩子也收进 nxt。本题只要值，混进 None 会在下一轮取
     node.val 时炸；需要靠 None 占位看出树形的是 BM35，那是另一个取舍。
  4. 空树是合法输入（n 可以为 0），期望 [] 而不是 [[]]。少了空树守卫，
     cur = [None] 会让第一轮就在 node.val 上抛 AttributeError。
  5. 循环终止靠「某层为空」，不是靠计数。树高事先未知，写死层数必然出错。
"""
from typing import List, Optional


class Solution:
    def levelOrder(self, root: "Optional[TreeNode]") -> List[List[int]]:
        # n 可以为 0；空树的答案是 []，不是 [[]]
        if root is None:
            return []
        out: List[List[int]] = []
        cur = [root]                      # cur 永远正好是「完整的一层」
        while cur:                        # 某层为空即到底，层数事先未知
            out.append([node.val for node in cur])
            # 整层重建：把这一层的非空孩子按从左到右收成下一层
            nxt: List["TreeNode"] = []
            for node in cur:
                if node.left is not None:
                    nxt.append(node.left)
                if node.right is not None:
                    nxt.append(node.right)
            cur = nxt
        return out
