import zipfile
import commons
import os
import shutil
import json
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

def find_dependencies_cmakes(project_path: str, workspace_dir: str) -> list[str]:
    VCPKG_JSON_PATH = f"{project_path}/vcpkg.json"
    with open(VCPKG_JSON_PATH, "r", encoding="utf-8") as f:
        vcpkg_json = json.load(f)

    exec_path = commons.realpath(_VCPKG_EXE)
    if exec_path.startswith(workspace_dir):
        search_dir = _get_vcpkg_dependencies_dir(workspace_dir)
    else:
        search_dir = os.path.dirname(exec_path)

    dependencies_list: list[str] = [dep.lower() for dep in vcpkg_json["dependencies"]]

    result_list: list[str] = []
    for path in pathlib.Path(search_dir).rglob('*Config.cmake'):
        path_str = path.parent.__str__()
        lowercased_path = path_str.lower()
        for dep in dependencies_list:
            if dep in lowercased_path:
                result_list.append(path_str)
                break
    return result_list