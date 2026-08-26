# 来源: 牛客 · 面试必刷TOP101　中等
# 链接: https://www.nowcoder.com/practice/55fb3c68d08d46119f76ae2df7566880
# 判题: 核心代码模式
# 签名: solve(IP: string) -> string

"""BM85 验证IP地址 —— 按分隔符分流，再把题面的每条规则逐条翻译成逐段体检。

这题考什么：
    没有算法成分，考的是把一份自然语言规格**不重不漏**地落成判断，
    以及分清哪些规则在 IPv4 与 IPv6 之间恰好相反。
    题面开头声明「本题对 IPv4、IPv6 的描述若和真实情况有出入，以本题描述为准」，
    所以一切以题面为准，不要凭 RFC 的印象补规则：
    真实世界的 IPv6 允许用 "::" 缩写连续的零段，本题明确判它不合法。

    先按分隔符分流：含 "." 走 IPv4 校验，含 ":" 走 IPv6 校验，
    两条都不通过就是 Neither。

    IPv4：用 "." 切开必须**恰好 4 段**，每段满足

        非空                     "1..1.1"          -> Neither
        只含 0-9                 "1.1.1.a"         -> Neither
        长度 <= 3                "1.1.1.1234"      -> Neither
        无前导零（"0" 本身合法）  "172.16.254.01"   -> Neither
        数值 0 <= x <= 255       "256.256.256.256" -> Neither

    IPv6：用 ":" 切开必须**恰好 8 段**，每段长度落在 1..4 之间，
    且只含十六进制字符 0-9 / a-f / A-F，大小写都认。
    长度下限 1 挡住空段（也就是题面点名的 "::"），
    长度上限 4 挡住「多余的 0」（"02001" 有 5 位）。

    段内前导零在 IPv6 里是**允许**的（"0db8"、"0" 都合法），与 IPv4 恰好相反，
    这是两套规则最容易互相写串的一处。

数据规模与复杂度：
    串长 5 <= n <= 50，时限「其他语言 2 秒」，规模上毫无压力：
    时间 O(n)、空间 O(n)（切分出来的那几段）。
    这题的失分全在规则覆盖度上——通过率 18%，低于同题单里不少算法题，
    掉的分几乎都是漏判某一条边界。

坑在哪：
  1. 判十进制数字不要用 str.isdigit()：它对 "²"、"١" 这类 Unicode 数字字符
     也返回 True，后面的 int() 未必吃得下。对着显式字符集判既稳妥，
     又不依赖运行环境的 locale。
  2. IPv4 的前导零判断必须写成「首位是 0 且长度大于 1」两个条件相与。
     只判首位是 0 会把合法的单个 "0" 毙掉；只判数值范围则拦不住 "01"。
  3. IPv6 段长的下限与上限对应两条**独立**的题面规则（不许空段、不许多余的 0），
     漏掉任何一边就会放过 "2001:0db8:85a3::8A2E:0370:7334"
     或 "02001:0db8:85a3:0000:0000:8a2e:0370:7334"。
  4. 段数判断顺手覆盖了首尾分隔符："1.1.1.1." 会切出 5 段，段数关就过不去，
     不必再额外写 startswith / endswith 的判断。
  5. 分流用 in 而不是二选一：一个串同时含 "." 和 ":" 时两套校验都会跑，
     但 IPv4 要求每段只含数字（不可能带冒号），两边不可能同时通过，
     最终仍正确地落到 Neither。
"""
from typing import List, Optional

# 字符集用集合而非字符串，判 in 是 O(1) 哈希查找；两张表在模块层只建一次
DIGITS = set("0123456789")
HEX = set("0123456789abcdefABCDEF")


class Solution:
    def solve(self, IP: str) -> str:
        if not IP:
            return "Neither"
        # 按分隔符分流：两种地址的字符集互斥，先试哪一种都不会误判
        if "." in IP and self._is_ipv4(IP):
            return "IPv4"
        if ":" in IP and self._is_ipv6(IP):
            return "IPv6"
        return "Neither"

    def _is_ipv4(self, ip: str) -> bool:
        parts = ip.split(".")
        # 恰好 4 段：这一条同时挡住了空段过多与首尾多余的分隔符（"1.1.1.1." 切出 5 段）
        if len(parts) != 4:
            return False
        for p in parts:
            if not p or len(p) > 3:
                return False
            # 不用 isdigit()：它对 Unicode 数字字符也为真，而 int() 未必接受
            if any(c not in DIGITS for c in p):
                return False
            if p[0] == "0" and len(p) > 1:      # 前导零不合法，单个 "0" 本身可以
                return False
            if int(p) > 255:
                return False
        return True

    def _is_ipv6(self, ip: str) -> bool:
        parts = ip.split(":")
        # 恰好 8 组，题面不允许用 "::" 缩写，段数必须自己凑齐
        if len(parts) != 8:
            return False
        for p in parts:
            # 下限 1 挡住空段（即 "::"），上限 4 挡住多余的 0（"02001" 有 5 位）
            if not 1 <= len(p) <= 4:
                return False
            # 与 IPv4 相反，这里允许前导零，只校验字符集
            if any(c not in HEX for c in p):
                return False
        return True
