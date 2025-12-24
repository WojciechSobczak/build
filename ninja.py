import os
import shutil
import urllib
import zipfile
import platform
import urllib.request

from . import commons
from . import log


"""
Ninja default structure for this configuration looks like this:

For 1.13.2
WINDOWS:
WORKSPACE_DIR/ninja:
    - ninja.exe

LINUX:
WORKSPACE_DIR/ninja:
    - ninja
"""

def _ninja_1_13_2_get_exec_path(workspace_dir: str) -> str:
    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{workspace_dir}/ninja/ninja{exe_ext}'

def _ninja_1_13_2_download(workspace_dir: str) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.error(f"Unsupported system: {platform.system()}")
        exit(-1)

    system_string = "win" if commons.is_windows() else "linux"
    link = f"https://github.com/ninja-build/ninja/releases/download/v1.13.2/ninja-{system_string}.zip"
    
    extract_path = f'{workspace_dir}/ninja'
    archive_path = f'{workspace_dir}/ninja-1.13.2.zip'

    if os.path.exists(extract_path):
        log.info("Previous ninja download exists. Deleting...")
        commons.delete_dir(extract_path)

    log.info("Downloading ninja executable...")
    urllib.request.urlretrieve(link, archive_path)
    log.info("Ninja downloaded.")

    log.info("Unpacking ninja executable...")
    with zipfile.ZipFile(archive_path, 'r') as zip_file:
        zip_file.extractall(extract_path)
    log.info("Unpacked ninja executable.")

    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{extract_path}/ninja{exe_ext}'

def download_ninja(workspace_dir: str) -> str:
    return _ninja_1_13_2_download(workspace_dir)

def is_ninja_systemwide_installed() -> bool:
    return shutil.which("ninja") != None

def is_ninja_in_workspace_toolset(workspace_dir: str) -> bool:
    return os.path.exists(_ninja_1_13_2_get_exec_path(workspace_dir))

def get_toolset_ninja_exe_path(workspace_dir: str) -> str:
    return _ninja_1_13_2_get_exec_path(workspace_dir)
