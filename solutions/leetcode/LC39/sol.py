"""LC39 组合总和 —— 排序后按下标不回头地选，同一个数允许重选，凑够 target 就收一份。

这题考什么：
    「组合」与「排列」的分界：[2,2,3] 与 [3,2,2] 是同一个组合，只能产出一次。
    去重的标准手法是给搜索强加一个顺序——**每层只从下标 start 开始往后选**，
    于是产出的每条组合内部都是不降的，同一批数字只会以唯一一种排列出现。

    本题的特殊之处是同一个数可以无限重复使用，所以递归时传的是 i 而不是 i + 1：
        dfs(i, remain)   下一层还能再选一次下标 i 的数
        dfs(i + 1, ...)  才是每个数最多用一次的写法（那是 LC40 的形态）
    这一个字之差就是「可重复选」与「不可重复选」的全部区别。

        candidates = [2,3,6,7], target = 7
        选 2 -> 剩 5 -> 再选 2 -> 剩 3 -> 选 3 -> 剩 0   收 [2,2,3]
                                      -> 选 6 超了，剪
             -> 选 3 -> 剩 2，但只能从 3 往后选，最小的 3 也超了，剪
        选 7 -> 剩 0                                     收 [7]

    先排序换来一条强剪枝：候选升序时，一旦 candidates[i] > remain，
    它后面的只会更大，整个 for 循环可以直接 break 而不是 continue。
    回溯的「选择 -> 递归 -> 撤销」三步见 docs/search/dfs.md。

数据规模与复杂度：
    1 <= candidates.length <= 30，2 <= candidates[i] <= 40，1 <= target <= 40，
    且题面保证答案不足 150 条。
    因为每个数至少是 2，递归深度不超过 target / 2 = 20 层。
    搜索树的结点数上界是 O(候选数 的 (target/最小值) 次方)，但排序 + break 剪枝
    把绝大多数分支在第一层就砍掉，实测规模远小于理论上界；
    题面给出的「答案少于 150 条」也从侧面担保了搜索树不会爆。
    每收一条答案要拷贝一份长度 O(target/最小值) 的列表，总时间在万级基本操作以内。
    空间 O(target / 最小值) 存 path 与递归栈。

坑在哪：
  1. 递归传 i 还是 i + 1，决定了数字能否复用。传 i + 1 会漏掉 [2,2,3]，
     示例 1 只剩 [7]；传 0（每层从头选）则会把 [2,2,3] 与 [3,2,2] 都吐出来，
     变成排列而非组合，重复解直接判错。
  2. 剪枝用 break 而不是 continue，前提是**已经排好序**。
     忘了 sorted 直接 break，遇到 [7,2,3] 这种输入会在第一个 7 就整层退出，
     漏掉全部以 2 开头的解——这个错在有序输入的样例上完全暴露不出来。
  3. 出口只判 remain == 0。不必再单独判 remain < 0：
     循环里 candidates[i] > remain 的分支已经被 break 掉，remain 永远不会变负。
  4. 收答案必须写 path[:] 做一份拷贝。path 是全程复用的同一个列表，
     直接追加它本身的话，res 里存的全是同一个对象的引用，
     回溯结束时 path 已被弹空，输出会变成一堆空列表。
  5. 撤销（path.pop）必须紧跟在递归之后，且与 append 一一配对。
     漏掉一处，兄弟分支就会带着上一条分支的残留数字继续累加。
  6. 本题在 meta.json 的 judge 里配了 unordered_deep：题面明写「可以按任意顺序返回」，
     组合之间没有先后语义；而每条组合是一个**集合**语义的多重集，
     [2,2,3] 与 [3,2,2] 表示同一组候选，所以内层顺序也一并放宽。
     放宽的只是顺序，不是内容——同一个组合吐两遍照样判错，去重仍靠上面那条 start 下标。

样例复核：
    示例 2 的 [2,3,5]、target = 8，按不降顺序枚举得 [2,2,2,2]、[2,3,3]、[3,5]，
    共 3 条，与样例一致；示例 3 的 [2]、target = 1 里第一层就有 2 > 1 触发 break，
    返回空列表。
"""
from typing import List, Optional


class Solution:
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        # 升序是下面 break 剪枝成立的前提：后面的数只会更大，不必再试
        candidates = sorted(candidates)
        n = len(candidates)
        # res 收答案，path 是当前正在拼的那条组合
        res = []
        path = []

        def dfs(start: int, remain: int) -> None:
            # 剩余额度归零即凑成一条；path[:] 是必需的拷贝，path 本身还要继续被改
            if remain == 0:
                res.append(path[:])
                return
            # 只从 start 往后选，强制组合内部不降，从根上杜绝 [2,2,3] / [3,2,2] 的重复
            for i in range(start, n):
                # 升序下这个数已经超额，后面的更大，整层直接停（continue 会白扫一遍）
                if candidates[i] > remain:
                    break
                path.append(candidates[i])          # 选
                # 递归传 i 而不是 i + 1：下一层还能再选中同一个数，这才是「可重复选取」
                dfs(i, remain - candidates[i])
                path.pop()                          # 撤销，让这一位换成下一个候选

        dfs(0, target)
        return res
