import datetime

def _now_str() -> str:
    return datetime.datetime.now().isoformat(sep=" ", timespec='milliseconds')

def error(msg: str):
    print(f"[BUILD_TOOLS][{_now_str()}][ERROR] {msg}")

def info(msg: str):
    print(f"[BUILD_TOOLS][{_now_str()}][INFO] {msg}")

def warn(msg: str):
    print(f"[BUILD_TOOLS][{_now_str()}][WARNING] {msg}")
