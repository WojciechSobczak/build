import datetime

def error(str: str):
    print(f"[BUILDTOOLS][{datetime.datetime.now()}][ERROR] {str}")

def info(str: str):
    print(f"[BUILDTOOLS][{datetime.datetime.now()}][INFO] {str}")