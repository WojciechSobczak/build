import os
import subprocess
import re
import platform
import log

def normalize_path(path: str) -> str:
    path = path.replace('\\', '/')
    path = re.sub('\\/+', '/', path)
    return path

def realpath(path: str) -> str:
    path = os.path.realpath(path)
    return normalize_path(path)

def execute_command(command: str, cwd: str, env = None):
    if cwd is None:
        raise Exception("'cwd' must be set")
    log.info(f"Executing: {command} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, shell=True, env=env)
    if process.returncode != 0:
        log.info(f"Command {command} failed with code: {process.returncode}")
        exit(-1)
    
def execute_process(command: list[str], cwd: str, env = None):
    if cwd is None:
        raise Exception("'cwd' must be set")
    log.info(f"Executing: {' '.join(command)} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, env=env)
    if process.returncode != 0:
        log.info(f"Command {' '.join(command)} failed with code: {process.returncode}")
        exit(-1)
    
def is_windows() -> bool:
    return platform.system() == "Windows"

def is_linux() -> bool:
    return platform.system() == "Linux"