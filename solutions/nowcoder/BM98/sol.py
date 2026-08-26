# 来源: 牛客 · 面试必刷TOP101　简单
# 链接: https://www.nowcoder.com/practice/7edf70f2d29c4b599693dc3aaeea1d31
# 判题: 核心代码模式
# 签名: spiralOrder(matrix: integer[][]) -> list<integer>

"""BM98 螺旋矩阵 —— 用上下左右四条边界圈住未访问区域，走一圈收一圈。

这题考什么：
    模拟题的状态设计。与其在矩阵里模拟「撞墙就转向」（那需要一个 visited 数组
    或方向表来判断何时转弯），不如直接维护四条**边界**
    top / bottom / left / right，让它们框住「还没输出的那块矩形」。
    每一圈按固定顺序走四条边，走完一条就把对应的边界往里收一格：

        沿 top 行从 left 到 right（向右）      走完 top += 1
        沿 right 列从 top 到 bottom（向下）    走完 right -= 1
        沿 bottom 行从 right 到 left（向左）   走完 bottom -= 1
        沿 left 列从 bottom 到 top（向上）     走完 left += 1

    四条边界一收，剩下的仍是一块矩形，于是同一段逻辑可以直接套用到下一圈，
    循环条件就是这块矩形还非空：top <= bottom and left <= right。
    转向不再需要判断，顺序是写死的；visited 数组也省掉了。

    走 3x3 的示例：

        1 2 3     向右 1 2 3     top=1
        4 5 6     向下 6 9       right=1
        7 8 9     向左 8 7       bottom=1
                  向上 4         left=1
                  剩下正中一格，下一圈 top=bottom=left=right=1，向右输出 5
        结果 [1,2,3,6,9,8,7,4,5]

数据规模与复杂度：
    0 <= n, m <= 10，元素绝对值 <= 100，时限「其他语言 2 秒」，
    题面要求时间 O(nm)、空间 O(nm)。
    每个元素恰好被输出一次，时间 O(nm)；除了结果列表没有任何额外标记，
    空间 O(nm) 全花在返回值上。规模极小，这题考的完全是边界处理的严谨度。

坑在哪：
  1. **关键陷阱在后两条边**。走完前两条边之后，四条边界可能已经交错，
     此时若不加判断就往回走，会把同一行或同一列**重复输出**。
     所以第三步之前要检查 top <= bottom，第四步之前要检查 left <= right。
  2. 单行矩阵 [[1,2,3]] 就是第三步的反例：向右输出 1,2,3 后 top 变成 1，
     已经大于 bottom = 0；向下那一步的 range 为空没有影响，
     但向左那一步若不拦，会沿着同一行倒着补出 2,1
     （right 此时已经收成 1，所以多出来的是两个而不是三个）。
  3. 单列矩阵 [[1],[2],[3]] 是第四步的反例：向右输出 1、向下输出 2,3 之后
     right 收成 -1，向左那一步的 range 为空，
     但向上那一步若不拦，会再输出一次 2。
  4. 三个向内的循环各有一处下标细节：向右与向下的 range 右端要写成
     right + 1、bottom + 1（Python 的 range 右端开区间，少加 1 就会漏掉最后一格）；
     向左与向上是倒序，range 的终点要写成 left - 1、top - 1，
     步长 -1，同样是为了让端点被取到。
  5. matrix 为 []（样例 2）或 [[]] 时直接返回空列表，
     否则 len(matrix[0]) 会在空矩阵上越界。
"""
from typing import List, Optional


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        # 空矩阵与 [[]] 都要挡住，否则下面取 matrix[0] 或它的长度会出错
        if not matrix or not matrix[0]:
            return []
        # 四条边界框住「还没输出的那块矩形」，全程保持它是一个矩形
        top, bottom = 0, len(matrix) - 1
        left, right = 0, len(matrix[0]) - 1
        res = []
        # 矩形非空就再走一圈；转向顺序写死，不需要方向表也不需要 visited
        while top <= bottom and left <= right:
            # 上边：从左到右。range 右端开区间，取 right + 1 才能覆盖最后一列
            for c in range(left, right + 1):
                res.append(matrix[top][c])
            top += 1                                  # 这一行走完，上边界内收
            # 右边：从上到下。起点已是内收后的 top，避免重复取拐角那一格
            for r in range(top, bottom + 1):
                res.append(matrix[r][right])
            right -= 1                                # 这一列走完，右边界内收
            # 下边：从右到左。前两次内收可能已让 top 越过 bottom，
            # 不加这道判断，单行矩阵会沿着同一行倒着再输出一遍
            if top <= bottom:
                for c in range(right, left - 1, -1):  # 倒序，终点取 left - 1 才能覆盖最左一格
                    res.append(matrix[bottom][c])
                bottom -= 1
            # 左边：从下到上。同理，不加判断单列矩阵会把同一列重复输出
            if left <= right:
                for r in range(bottom, top - 1, -1):  # 倒序，终点取 top - 1 才能覆盖最上一格
                    res.append(matrix[r][left])
                left += 1
        return res
