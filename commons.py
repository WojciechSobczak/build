import os
import subprocess
import re
import platform

from . import log # type: ignore

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
    cwd = realpath(cwd)
    log.info(f"Executing: {command} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, shell=True, env=env)
    if process.returncode != 0:
        log.info(f"Command {command} failed with code: {process.returncode}")
        exit(-1)
    
def execute_process(command: list[str], cwd: str, env = None):
    if cwd is None:
        raise Exception("'cwd' must be set")
    cwd = realpath(cwd)
    log.info(f"Executing: {' '.join(command)} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, env=env)
    if process.returncode != 0:
        log.info(f"Command {' '.join(command)} failed with code: {process.returncode}")
        exit(-1)

def delete_dir(dir_path: str):
    if os.path.isdir(dir_path) == False:
        log.error(f"delete_dir(): {dir_path} is not a directory")
        raise Exception(f"delete_dir(): {dir_path} is not a directory")
    dir_path = realpath(dir_path)

    command = []
    if is_windows():
        command += [f'del /f /s /q "{dir_path}"', f'rmdir /s /q "{dir_path}"']
    else:
        command += [f'rm -rf "{dir_path}"']
    execute_command(' && '.join(command), cwd=os.path.dirname(dir_path))


def rename_dir(source_dir_path: str, target_dir_path: str):
    if os.path.isdir(source_dir_path) == False:
        msg = f"rename_dir(): {source_dir_path} is not a directory"
        log.error(msg)
        raise Exception(msg)
    
    source_dir_path = realpath(source_dir_path)
    target_dir_path = realpath(target_dir_path)

    if is_windows():
        win_cwd = source_dir_path[:-1] if source_dir_path.endswith('/') else source_dir_path
        win_cwd = os.path.dirname(win_cwd)
        # If directories are in the same directory use 'ren' as its faster
        if os.path.dirname(source_dir_path) == os.path.dirname(target_dir_path):
            source_dir_path = source_dir_path[source_dir_path.rfind('/') + 1:]
            target_dir_path = target_dir_path[target_dir_path.rfind('/') + 1:]
            execute_command(f'ren "{source_dir_path}" "{target_dir_path}"', cwd=win_cwd)
        else:
            # With windows 'move' moved directory must be a cwd of a command because of reasons
            os.makedirs(target_dir_path, exist_ok=True)
            execute_command(f'move /y "{source_dir_path}" "{target_dir_path}"', cwd=win_cwd)
    else:
        execute_command(f'mv "{source_dir_path}" "{target_dir_path}"', cwd=source_dir_path)
    
def is_windows() -> bool:
    return platform.system() == "Windows"

def is_linux() -> bool:
    return platform.system() == "Linux"