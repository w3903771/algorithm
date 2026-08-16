"""PIO6 单组_一维数组 —— 先读长度 n，再读 n 个数。

要点：n 只是用来告诉你有多少个数，Python 里可以直接把整行 split 掉，
sum(map(int, ...)) 一步到位，比 for 循环累加快得多。
"""
input()                                   # n，Python 中用不上
print(sum(map(int, input().split())))
