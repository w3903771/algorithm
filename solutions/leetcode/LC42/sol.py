"""LC42 接雨水 —— 按列算水量，用相向双指针只维护两侧前缀最大值，O(1) 空间一趟扫完。

这题考什么：
    先把问题拆到**每一列**上。第 i 列头顶的水面高度，由它左边最高的柱子
    与右边最高的柱子中**较矮**的那根决定（水会从矮的一侧溢走）：

        water[i] = min(前缀最大值 leftMax[i], 后缀最大值 rightMax[i]) - height[i]

    这个量非负——leftMax 与 rightMax 都至少等于 height[i] 自己。
    把每列的 water 加起来就是答案。这叫「按列接」。

    照定义实现要预处理 leftMax 与 rightMax 两个数组，O(n) 时间、O(n) 空间。
    双指针把空间压到 O(1)，靠的是一个不对称的观察：

        维护 l 从左走、r 从右走，以及 left_max = max(height[0..l])、
        right_max = max(height[r..n-1])。
        每轮比较 height[l] 与 height[r]，结算较矮的那一侧那一列，然后让它前进。

    **为什么较矮那侧可以只看自己这边的最大值就结算**。设 height[l] < height[r]，
    要证的是 leftMax(l) <= 真正的 rightMax(l) = max(height[l+1 .. n-1])，
    这样 min 取的就是 leftMax(l)，右边具体怎么排布都不影响。分两种情形：

        leftMax(l) 就是 height[l] 自己
            rightMax(l) >= height[r] > height[l]，成立。
        leftMax(l) 来自某个更靠左的 p（height[p] > height[l]）
            l 之所以走过了 p，是因为当时那一轮取了左分支，
            即 height[p] < 当时的 height[r']，而 r' 只会比现在的 r 更靠右，
            所以 height[r'] 仍落在 [l+1, n-1] 里，rightMax(l) >= height[r']
            > height[p] = leftMax(l)，同样成立。

    也就是说：结算某一列时不必知道另一侧的确切最大值，只需要知道
    另一侧**不会成为短板**。这正是每步比较 height[l] 与 height[r] 换来的信息。
    相向双指针的一般套路见 docs/basic/two-pointer.md。

    另一条主流解法是**单调栈**（栈内元素保持单调不增，见
    docs/ds/monotonic-stack.md）：栈里存下标，
    遇到比栈顶高的柱子就说明找到了右边界，弹出栈顶当「凹槽底」，
    用左右两根柱子的较矮者减去槽底，乘以宽度，一次结算**一整层横条**。
    这叫「按行接」。两者的取舍：

        按列（双指针）  O(n) 时间 O(1) 空间，代码十来行，常数最小
        按行（单调栈）  O(n) 时间 O(n) 空间，多了栈的维护与宽度计算，
                        但它是「找每个元素左右第一个更大元素」这一类问题的
                        通用框架，迁移性强

    本题只要答案不要中间结构，按列的双指针是更好的选择。

数据规模与复杂度：
    1 <= n <= 2e4，0 <= height[i] <= 1e5。
    水量上界约 2e4 * 1e5 = 2e9，Python 整数不溢出。
    时间 O(n)：l 与 r 合计走 n 步；空间 O(1)。
    对每一列现算左右最大值是 O(n^2) = 4e8 次比较，Python 下超时。

坑在哪：
  1. 移动的是**较矮**的一侧，和 LC11 盛最多水的容器同一个方向，但理由不同：
     那题是「含这条边的最优解已取到」，这题是「短板在这一侧，
     水面已被 left_max 或 right_max 钉死，可以放心结算」。
     若移动较高的一侧，被结算那列的另一侧最大值还没扫到，
     min 取错，水量会算大。
  2. left_max / right_max 必须在结算**之前**更新。先算水量再更新，
     当前柱子若是新的最高点，会算出 left_max - height[l] 为负的水量。
     本题解的写法是先更新再相减，因此差值恒非负，不需要 max(0, ...) 兜底。
  3. 循环条件是 `while left < right`。用 `<=` 会让中间那一列被结算两次
     （左右指针都指着它），水量翻倍。
  4. n 为 1、2 或全是等高柱子时答案是 0。这不需要特判：
     每一步的 left_max - height[l] 都是 0，累加仍是 0。
  5. 严格比对：答案是一个整数，没有多解。

样例复核：
    height = [0,1,0,2,1,0,1,3,2,1,2,1]，n = 12，期望 6。
    按列算一遍（min(leftMax, rightMax) - height）：
        下标      0  1  2  3  4  5  6  7  8  9 10 11
        height    0  1  0  2  1  0  1  3  2  1  2  1
        leftMax   0  1  1  2  2  2  2  3  3  3  3  3
        rightMax  3  3  3  3  3  3  3  3  2  2  2  1
        水量      0  0  1  0  1  2  1  0  0  1  0  0
    合计 1 + 1 + 2 + 1 + 1 = 6，与样例一致。
    双指针走的是同一笔账，只是不把 leftMax / rightMax 整个存下来。
"""
from typing import List, Optional


class Solution:
    def trap(self, height: List[int]) -> int:
        left = 0
        right = len(height) - 1
        # 循环不变量（每轮**比较之前**成立）：left_max 是已越过的左段
        # height[0..left-1] 的最大值，right_max 是已越过的右段 height[right+1..n-1]
        # 的最大值；初始两段都为空，故取 0（题面保证高度非负，0 是安全的空集最大值）
        left_max = 0
        right_max = 0
        ans = 0
        # 用 < 而非 <=：相等时两侧指着同一列，会被结算两次
        while left < right:
            # height[left] < height[right] 时可证 left_max 不超过右侧真正的最大值
            # （见文档字符串的两情形讨论），于是第 left 列的水面被 left_max 钉死，
            # 右边怎么排布都不影响，可以当场结算。反之则对称地结算右侧
            if height[left] < height[right]:
                # 先更新再相减：这样差值恒非负，当前柱子若是新高点，水量自然是 0
                if height[left] > left_max:
                    left_max = height[left]
                ans += left_max - height[left]
                left += 1
            else:
                if height[right] > right_max:
                    right_max = height[right]
                ans += right_max - height[right]
                right -= 1
        return ans
