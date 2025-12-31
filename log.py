import datetime

def _now_str() -> str:
    return datetime.datetime.now().isoformat(sep=" ", timespec='milliseconds')

def error(str: str):
    print(f"[BUILDTOOLS][{_now_str()}][ERROR] {str}")

def info(str: str):
    print(f"[BUILDTOOLS][{_now_str()}][INFO] {str}")

def warn(str: str):
    print(f"[BUILDTOOLS][{_now_str()}][WARNING] {str}")