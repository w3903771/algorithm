"""PIO2 单组_A+B —— 单组数据，一行两个整数。

要点：input().split() 拿到字符串列表，map(int, ...) 批量转 int，再解包。
"""
a, b = map(int, input().split())
print(a + b)
