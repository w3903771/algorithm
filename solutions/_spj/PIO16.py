"""PIO16 校验器：YES/NO 大小写任意。"""


def check(inp: str, out: str) -> bool:
    n = int(inp.split()[0])
    want = "YES" if n % 2 else "NO"
    return out.strip().upper() == want
