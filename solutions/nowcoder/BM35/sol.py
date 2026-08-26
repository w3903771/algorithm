# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/8daa4dff9e36409abba2adbe413d6fae
# 判题: 核心代码模式
# 签名: isCompleteTree(root: TreeNode) -> boolean

"""BM35 判断是不是完全二叉树 —— 层序遍历把空孩子也入队，见到第一个空之后不许再出现非空。

这题考什么：
    完全二叉树的定义是「除最后一层外每层都填满，最后一层的叶子连续集中在
    最左边」。逐条去核对层数和每层节点个数很啰嗦，换成层序编号的视角就只剩
    一句话：按层序编号 1..n 逐位填，中间**不留洞**。

    把空孩子也一并入队，这个「洞」就直接暴露在序列里了：

        完全的 {1,2,3,4,5,6}     层序（含空）: 1 2 3 4 5 6 # # # # # #
                                              非空全在前，空全在后，合格

        不完全的 {1,2,3,4,5,#,6} 层序（含空）: 1 2 3 4 5 # 6 ...
                                                        第一个空后面又冒出 6，不合格

    于是判据就是：**遇到第一个 None 之后，队列里不能再出现非空节点**。
    代码写成两个阶段：
      1. 正常层序，允许 None 入队，直到弹出一个 None 就跳出——
         此时已经确认前半段全是非空的；
      2. 把队列剩下的元素排干，只要还能碰到非空节点就返回 False；
         排干后仍没碰到，说明空位全挤在末尾。

数据规模与复杂度：
    1 <= n <= 100；时限「其他语言 2 秒」。
    n 个节点各贡献两个孩子槽位，队列一共处理 O(n) 个元素，时间 O(n)；
    空间 O(w)，w 为最宽一层的规模。

坑在哪：
  1. **入队时不能过滤 None**。写成 `if child is not None: queue.append(child)`
     就把「洞」抹平了，{1,2,3,4,5,#,6} 与 {1,2,3,4,5,6} 会得到同一个序列，
     前者被误判成 true。这与 BM26 的取舍正好相反：那题只要值，None 是噪音；
     这题要的就是形状，None 是唯一的信息来源。
  2. 第一阶段碰到 None 只能 break，**不能直接返回 True**。判定的后半句
     「后面不许再有非空」全靠第二阶段把队列排干才能验证；漏掉第二阶段，
     示例 3 的 {1,2,3,4,5,#,6} 会被判成 true。
  3. 判空写 `is not None`。第二阶段若写成 `if queue.popleft():`，节点对象
     恒为真、None 为假，这一处碰巧等价，但依赖对象真值不是可靠写法。
  4. 空树按定义算完全二叉树。题面写 n >= 1，守卫仍然保留：少了它
     queue = deque([None])，第一阶段立刻 break，第二阶段队列已空，
     返回值虽然仍是 True，但那是巧合而非有意为之。
  5. 队列用 collections.deque。n <= 100 时拿 list 当队列也跑得完，但
     list.pop(0) 要把剩余元素整体前移，是 O(n) 一次；deque.popleft() 是
     O(1)，见 docs/search/bfs.md 的 61.2 节。
"""
import collections
from typing import List, Optional


class Solution:
    def isCompleteTree(self, root: "Optional[TreeNode]") -> bool:
        # 空树按定义是完全二叉树
        if root is None:
            return True
        queue = collections.deque([root])
        while queue:                          # 第一阶段：走到第一个空位为止
            node = queue.popleft()
            if node is None:
                break                         # 只能 break：后半段还得验
            # 空孩子照样入队——「洞」就是靠这些占位才看得见
            queue.append(node.left)           # 空孩子也入队，用来占位
            queue.append(node.right)
        while queue:                          # 第二阶段：后面必须全是空位
            if queue.popleft() is not None:
                return False                  # 空位之后又出现节点，中间有洞
        return True
