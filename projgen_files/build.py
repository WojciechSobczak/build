import sys
import re
import os
import subprocess

def normalize_path(path: str):
    path = path.replace('\\', '/')
    path = re.sub('\\/+', '/', path)
    return path

def realpath(path: str):
    path = os.path.realpath(path)
    return normalize_path(path)

BASE_PATH = realpath(os.path.dirname(os.path.realpath(__file__)))

def execute_process(command: list[str]):
    print(f"Executing: {' '.join(command)} | CWD: {BASE_PATH}")
    process = subprocess.run(args=command, cwd = BASE_PATH)
    if process.returncode != 0:
        raise Exception(f"Non zero return code: {process.returncode}")


def main():
    build_args = [
        "python3", "${script_name}",
        "-w", "${project_path}",
        "--package-manager", "${package_manager}"
    ]
    if len(sys.argv) >= 2:
        build_args += sys.argv[1:]
    execute_process(build_args)

if __name__ == "__main__":
    main()