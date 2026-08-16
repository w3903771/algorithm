"""PIO15 单组_补充前导零 —— 补足 9 位。

要点：zfill(9) 或 f"{n:09d}" 都可以，前者更直白。
"""
print(input().strip().zfill(9))
