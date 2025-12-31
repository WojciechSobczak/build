import os
import subprocess
import re
import platform
import functools
import typing

from . import log

def _error_log_and_die(msg: str) -> typing.NoReturn:
    log.error(msg)
    exit(-1)

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
        log.info(f"Command: {command} failed with code: {process.returncode}")
        exit(process.returncode)
    
def execute_process(command: list[str], cwd: str, env = None, return_stdout: bool = False) -> str | None:
    if cwd is None:
        raise Exception("'cwd' must be set")
    cwd = realpath(cwd)
    log.info(f"Executing: {' '.join(command)} | CWD: {cwd}")
    process = subprocess.run(args=command, cwd = cwd, env=env, stdout=subprocess.PIPE if return_stdout else None)
    if process.returncode != 0:
        log.info(f"Command: {' '.join(command)} failed with code: {process.returncode}")
        exit(process.returncode)
    if return_stdout == False:
        return None
    if process.stdout == None:
        return ""
    return process.stdout.decode("utf-8")


def delete_dir(dir_path: str, suppress_output: bool = True):
    if os.path.isdir(dir_path) == False:
        _error_log_and_die(f"delete_dir(): {dir_path} is not a directory")

    dir_path = realpath(dir_path)
    command = []
    if is_windows():
        null_redirect = '> nul' if suppress_output else ''
        command += [f'del /f /s /q "{dir_path}" {null_redirect}', f'rmdir /s /q "{dir_path}"']
    else:
        command += [f'rm -rf "{dir_path}"']
    execute_command(' && '.join(command), cwd=os.path.dirname(dir_path))

def rename_dir(source_dir_path: str, target_dir_name: str):
    if os.path.isdir(source_dir_path) == False:
        _error_log_and_die(f"rename_dir(): source_dir_path: {source_dir_path} is not a directory")

    # Some checks to avoid problems, not full check as no idea how
    if ('/' in target_dir_name) or ('\\' in target_dir_name):
        _error_log_and_die(f"rename_dir(): target_dir_name: {target_dir_name} must be a plain name")
    
    # Get real path, remove trailing / and get directory name and parent directory
    source_dir_path = realpath(source_dir_path)
    source_dir_path = source_dir_path[:-1] if source_dir_path.endswith('/') else source_dir_path
    source_dir_name = source_dir_path[source_dir_path.rfind('/') + 1:]
    source_dir_parent_path = os.path.dirname(source_dir_path)
    if is_windows():
        execute_process(["powershell", "-Command", "Rename-Item", "-Path", source_dir_name, "-NewName", target_dir_name], cwd=source_dir_parent_path)
    else:
        execute_process(["mv", source_dir_name, target_dir_name], cwd=source_dir_parent_path)

@functools.cache
def is_windows() -> bool:
    return platform.system() == "Windows"

@functools.cache
def is_linux() -> bool:
    return platform.system() == "Linux"