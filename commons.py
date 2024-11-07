import os
import subprocess
import re

def normalize_path(path: str):
    path = path.replace('\\', '/')
    path = re.sub('\\/+', '/', path)
    return path

def realpath(path: str):
    path = os.path.realpath(path)
    return normalize_path(path)

def execute_command(command: str, cwd: str, env = None):
    if cwd is None:
        raise Exception("'cwd' must be set")
    print(f"Executing: {command} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, shell=True, env=env)
    if process.returncode != 0:
        raise Exception(f"Non zero return code: {process.returncode}")
    
def execute_process(command: list[str], cwd: str, env = None):
    if cwd is None:
        raise Exception("'cwd' must be set")
    print(f"Executing: {' '.join(command)} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, env=env)
    if process.returncode != 0:
        raise Exception(f"Non zero return code: {process.returncode}")