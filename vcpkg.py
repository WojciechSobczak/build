import zipfile
import commons
import os
import shutil
import platform
import urllib.request
import pathlib

_VCPKG_EXE: str = ""
_VCPKG_VERSION: str = "2025.04.09"
_VCPKG_TOOL_VERSION: str = "2025-04-16"

def set_exec_file(vcpkg_exe: str):
    global _VCPKG_EXE
    _VCPKG_EXE = vcpkg_exe

def is_vcpkg_in_path():
    return shutil.which("vcpkg") != None

def _get_vcpkg_exec_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg_exec'

def _get_vcpkg_unpacked_dir(workspace_dir: str) -> str:
    return f'{_get_vcpkg_exec_dir(workspace_dir)}/vcpkg-{_VCPKG_VERSION}'

def _get_vcpkg_dependencies_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/dependencies/vcpkg'

def download_vcpkg(workspace_dir: str):
    vcpkg_exec_dir = _get_vcpkg_exec_dir(workspace_dir)
    vcpkg_code_zip = f'{vcpkg_exec_dir}/vcpkg.zip'
    vcpkg_exec_path = f'{vcpkg_exec_dir}/vcpkg.exe'

    if os.path.exists(vcpkg_exec_path):
        return vcpkg_exec_path
    
    os.makedirs(vcpkg_exec_dir, exist_ok=True)
    
    source_code_zip_url = f"https://github.com/microsoft/vcpkg/archive/refs/tags/{_VCPKG_VERSION}.zip"
    urllib.request.urlretrieve(source_code_zip_url, vcpkg_code_zip)
    with zipfile.ZipFile(vcpkg_code_zip, 'r') as zip_file:
        zip_file.extractall(vcpkg_exec_dir)

    exec_url = f"https://github.com/microsoft/vcpkg-tool/releases/download/{_VCPKG_TOOL_VERSION}/vcpkg.exe"
    print(exec_url)
    urllib.request.urlretrieve(exec_url, vcpkg_exec_path)

    return vcpkg_exec_path

def install_dependencies(project_dir: str, workspace_dir: str):
    dependencies_folder = f'{workspace_dir}/dependencies/vcpkg'
    os.makedirs(dependencies_folder, exist_ok=True)

    env = os.environ.copy()
    env['VCPKG_ROOT'] = _get_vcpkg_unpacked_dir(workspace_dir)

    commons.execute_process([
        _VCPKG_EXE, "install", 
        "--x-install-root", dependencies_folder,
        "--x-buildtrees-root", dependencies_folder,
        "--x-packages-root", dependencies_folder,
    ], project_dir, env)

def find_dependencies_cmakes(workspace_dir: str) -> list[str]:
    search_dir = _get_vcpkg_dependencies_dir(workspace_dir)
    result_list: list[str] = []
    for path in pathlib.Path(search_dir).rglob('*Config.cmake'):
        result_list.append(path.parent.__str__())
    return result_list