import platform
import zipfile
import os
import shutil
import urllib.request
import json

from . import commons
from . import log

"""
vcpkg default structure for this configuration looks like this:

For 2025.11.19
WINDOWS:
    WORKSPACE_DIR/vcpkg:
        - vcpkg.exe
        - vcpkg-triplets
            - <github repo>
        - dependencies
LINUX:
    WORKSPACE_DIR/vcpkg:
        - vcpkg
        - vcpkg-triplets
            - <github repo>
        - dependencies
"""

def _vcpkg_2025_11_19_get_exec_path(workspace_dir: str) -> str:
    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{workspace_dir}/vcpkg/vcpkg{exe_ext}'

def _vcpkg_2025_10_17_get_triplets_path(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg/vcpkg-triplets'

def _vcpkg_2025_11_19_exec_download(workspace_dir: str) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.error(f"Unsupported system: {platform.system()}")
        exit(-1)

    if commons.is_windows():
        link = f"https://github.com/microsoft/vcpkg-tool/releases/download/2025-11-19/vcpkg.exe"
    else:
        link = "https://github.com/microsoft/vcpkg-tool/releases/download/2025-11-19/vcpkg-glibc"
    extract_path = f'{workspace_dir}/vcpkg'
    exe_ext = ".exe" if commons.is_windows() else ""
    exec_path = f'{extract_path}/vcpkg{exe_ext}'

    log.info("Downloading vcpkg executable...")
    os.makedirs(os.path.dirname(exec_path), exist_ok=True)
    urllib.request.urlretrieve(link, exec_path)
    log.info("vcpkg executable downloaded")

    return exec_path

def _vcpkg_2025_10_17_triplets_download(workspace_dir: str):
    link = f"https://github.com/microsoft/vcpkg/archive/refs/tags/2025.10.17.zip"
    archive_path = f'{workspace_dir}/vcpkg-triplets-2025.10.17.zip'
    extract_path = f'{workspace_dir}/vcpkg'
    extracted_path = f'{workspace_dir}/vcpkg/vcpkg-2025.10.17'
    unified_extracted_path = f'{workspace_dir}/vcpkg/vcpkg-triplets'

    if os.path.exists(extract_path):
        log.info("Previous vcpkg download exists. Deleting...")
        commons.delete_dir(extract_path)

    log.info("Downloading vcpkg triples...")
    urllib.request.urlretrieve(link, archive_path)
    log.info("vcpkg triples downloaded.")

    log.info("Unpacking vcpkg triples...")
    with zipfile.ZipFile(archive_path, 'r') as zip_file:
        zip_file.extractall(extract_path)
    log.info("vcpkg triples unpacked")

    log.info("Renaming vcpkg unpacked triples...")
    commons.rename_dir(extracted_path, unified_extracted_path)
    log.info("Renamed vcpkg unpacked triples folder.")

def is_vcpkg_systemwide_installed() -> bool:
    return shutil.which("vcpkg") != None

def is_vcpkg_in_workspace_toolset(workspace_dir: str) -> bool:
    exe_present = os.path.exists(_vcpkg_2025_11_19_get_exec_path(workspace_dir))
    triplets_present = os.path.exists(_vcpkg_2025_10_17_get_triplets_path(workspace_dir))
    return exe_present and triplets_present

def get_toolset_vcpkg_exe_path(workspace_dir: str) -> str:
    return _vcpkg_2025_11_19_get_exec_path(workspace_dir)

def get_triplets_path(workspace_dir: str) -> str:
    return _vcpkg_2025_10_17_get_triplets_path(workspace_dir)

def get_vcpkg_dependencies_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg/dependencies'

def download_vcpkg(workspace_dir: str):
    _vcpkg_2025_10_17_triplets_download(workspace_dir)
    return _vcpkg_2025_11_19_exec_download(workspace_dir)

def try_to_find_dependencies(workspace_dir: str, project_dir: str) -> list[str]:
    json_path = f'{project_dir}/vcpkg.json'
    with open(json_path, "r", encoding="UTF-8") as file:
        json_string = file.read()
    deps_json = json.loads(json_string)

    json_deps_array: list[dict] = deps_json['dependencies']
    if type(json_deps_array) != list:
        msg = "vcpkg.json have invalid format. 'dependencies' must be an list of dicts"
        log.error(msg)
        raise Exception(msg)
    
    deps_to_look_for: set[str] = set()
    for json_dep in json_deps_array:
        if type(json_dep) != dict:
            msg = "vcpkg.json have invalid format. 'dependencies' must be an list of dicts"
            log.error(msg)
            raise Exception(msg)

        json_dep_name = json_dep['name']
        if json_dep_name == None:
            msg = "vcpkg.json have invalid format. 'dependencies/name' must be present and type str"
            log.error(msg)
            raise Exception(msg)
        deps_to_look_for.add(json_dep_name)

    vcpkg_deps_dir = get_vcpkg_dependencies_dir(workspace_dir)

    config_suffix = "config.cmake"
    def _find_deps():
        deps_found: set[str] = set()
        for directory, directory_names, file_names in os.walk(vcpkg_deps_dir):
            for file_name in file_names:
                low_file_name = file_name.lower()
                lib_name = low_file_name[0:-len(config_suffix)]
                if low_file_name.endswith(config_suffix) and lib_name in deps_to_look_for:
                    deps_to_look_for.remove(lib_name)
                    deps_found.add(commons.realpath(directory))
                    if len(deps_to_look_for) == 0:
                        return deps_found
        return deps_found
    return list(_find_deps())


def download_dependencies(vcpkg_executable: str, workspace_dir: str, project_dir: str):
    os.makedirs(get_vcpkg_dependencies_dir(workspace_dir), exist_ok=True)

    env = os.environ.copy()
    env['VCPKG_ROOT'] = get_triplets_path(workspace_dir)

    commons.execute_process([
        vcpkg_executable, "install", 
        "--x-install-root", get_vcpkg_dependencies_dir(workspace_dir),
        "--x-buildtrees-root", get_vcpkg_dependencies_dir(workspace_dir),
        "--x-packages-root", get_vcpkg_dependencies_dir(workspace_dir),
    ], project_dir, env)
