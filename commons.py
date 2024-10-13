import os
import shutil
import subprocess
import re

def normalize_path(path: str):
    path = path.replace('\\', '/')
    path = re.sub('\\/+', '/', path)
    return path

def realpath(path: str):
    path = os.path.realpath(path)
    return normalize_path(path)

BASE_PATH = realpath(os.path.dirname(os.path.realpath(__file__)))

def execute_command(command: str, cwd: str = None, env = None):
    if cwd is None:
        cwd = BASE_PATH
    print(f"Executing: {command} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, shell=True, env=env)
    if process.returncode != 0:
        raise Exception(f"Non zero return code: {process.returncode}")
    
def execute_process(command: list[str], cwd: str = None, env = None):
    if cwd is None:
        cwd = BASE_PATH
    print(f"Executing: {' '.join(command)} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, env=env)
    if process.returncode != 0:
        raise Exception(f"Non zero return code: {process.returncode}")