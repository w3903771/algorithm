# 来源: 牛客 · 面试必刷TOP101　较难
# 链接: https://www.nowcoder.com/practice/cf7e25aa97c04cc1a68c8f040e71fb84
# 判题: 核心代码模式
# 签名: 需实现 Serialize、Deserialize，判题走 driver.py

"""BM39 序列化二叉树 —— 前序遍历带空占位写成逗号串，反序列化按同样的前序顺序读回来。

这题考什么：
    题目不约束串的格式，只要求 Deserialize(Serialize(root)) 还原出一棵与原树
    相同的树。判题也是这么判的：driver.py 建好原树后，
    把 Serialize 的结果直接喂给 Deserialize，再把还原出的树和原树比结构，
    中间那个字符串**根本不参与比较**。所以格式随便挑，唯一的硬要求是
    「一个来回不丢信息」——两个方法必须严格咬合，各自单独看着合理没有意义。

    挑法上，前序 + 空节点占位是解析最省事的一种。

    为什么光有前序不够、必须补空占位：只有一个孩子时，孩子挂左还是挂右，
    前序序列完全一样。根 1 带一个孩子 2，无论 2 是左孩子还是右孩子，
    前序都是 1, 2。补上占位就区分开了：

        2 是左孩子   前序含空: 1, 2, #, #, #
        2 是右孩子   前序含空: 1, #, 2, #, #

    补空之后每个节点恰好贡献「自己 + 两个孩子槽位」，串和树一一对应，
    反序列化只要按同一顺序把槽位填回去。

    两个方向都写成显式状态机：
      - Serialize：栈里放节点（允许 None），弹出非空就输出值并压右、压左，
        弹出 None 就输出 #；出栈顺序即前序。
      - Deserialize：栈里放 [节点, 已填好的孩子个数]。看栈顶还缺左孩子就读一个
        token 填左，缺右孩子就填右，两个都填好就出栈；新建的非空孩子立刻压栈，
        于是读取顺序和序列化时的前序完全对齐。

数据规模与复杂度：
    n <= 100，节点值满足 0 <= val <= 150；时限「其他语言 2 秒」。
    两个方向都是每个节点、每个空槽位各处理一次，时间 O(n)；
    串长与栈深都是 O(n)，空间 O(n)，与题面要求一致。

坑在哪：
  1. **判的是往返一致，不是串本身**。驱动器不看格式，所以自定义格式是允许的；
     但也因此，Serialize 里多写一个空格、Deserialize 里少切一次，错误只会
     在还原出的树上暴露，看串是看不出来的。改动任一方都必须同步改另一方。
  2. **分隔符不能省**。值域到 150 是多位数，把 str(val) 直接拼在一起，
     "12" 到底是一个 12 还是 1 和 2 就分不清了。逗号分隔加 int() 还原是
     确定无歧义的。
  3. **Deserialize 的参数名 str 来自官方模板，遮蔽了内置的 str**。
     签名不能改，所以这个方法体内绝对不能再调用 str(...)——那会拿到传进来的
     字符串对象去调用，抛 TypeError: 'str' object is not callable。
     Serialize 是另一个作用域，那里的 str(node.val) 不受影响。
  4. **空树两端都要认**。Serialize 对 None 返回 "#"；Deserialize 收到 "#"
     或空串都还原成 None。少了任何一半，空树这个来回就断了。
  5. 栈帧用可变的 list 而不是 tuple。计数要在原地自增（frame[1] += 1），
     换成元组就得每次弹出再压回，写起来更绕也更容易漏。
  6. 「已填孩子数」等于 2 时先出栈再继续，这一步必须在读 token **之前**做，
     否则会把下一个 token 错填到一个已经满员的节点上。
  7. Serialize 压栈仍是「先右后左」。写反了出栈顺序变成「根 右 左」，
     而 Deserialize 是按「先左后右」填的，两边错位，还原出的树左右颠倒。
"""
from typing import List, Optional


class Solution:
    def Serialize(self, root: "Optional[TreeNode]") -> str:
        # 空树也要有确定的表示，否则 Deserialize 无从还原
        if root is None:
            return "#"
        out: List[str] = []
        stack: List[Optional["TreeNode"]] = [root]
        # 前序：弹出即输出，压栈先右后左；None 也压进去，弹出时写成占位符
        while stack:
            node = stack.pop()
            if node is None:
                out.append("#")               # 空槽位也要落到串里
                continue
            out.append(str(node.val))
            stack.append(node.right)          # 先压右，后压左 -> 弹出即前序
            stack.append(node.left)
        # 逗号分隔：值是多位数，直接拼接会让 12 和 1、2 混淆
        return ",".join(out)

    def Deserialize(self, str: str) -> "Optional[TreeNode]":
        # 参数名 str 来自官方模板，遮蔽了内置 str，这个方法体内不能再调用 str(...)
        tokens = str.split(",") if str else ["#"]
        if tokens[0] == "#":
            return None
        root = TreeNode(int(tokens[0]))
        stack = [[root, 0]]                   # [节点, 已经填好的孩子个数]
        i = 1
        while stack and i < len(tokens):
            frame = stack[-1]
            # 满员检查必须在读 token 之前，否则会把下一个值错填到已满的节点上
            if frame[1] == 2:                 # 左右都填完了，这个节点收工
                stack.pop()
                continue
            token = tokens[i]
            i += 1
            child = None if token == "#" else TreeNode(int(token))
            # 先左后右，与 Serialize 的前序顺序严格对齐
            if frame[1] == 0:
                frame[0].left = child
            else:
                frame[0].right = child
            frame[1] += 1
            if child is not None:             # 新节点接着往下读，正好是前序
                stack.append([child, 0])
        return root
