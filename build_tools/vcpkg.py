import platform
import typing
import zipfile
import os
import shutil
import urllib.request
import json

from . import commons
from . import log
from . import config

"""
vcpkg default structure for this configuration looks like this:

For 2025.11.19
WORKSPACE_DIR/vcpkg:
    - vcpkg.exe/elf
    - vcpkg-triplets
        - <github repo>
    - buildtrees
    - install
    - packages
"""

def _error_log_and_die(msg: str) -> typing.NoReturn:
    log.error(msg)
    exit(-1)

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
    downloaded_archive_path = f'{workspace_dir}/vcpkg-triplets-2025.10.17.zip'
    files_output_path = f'{workspace_dir}/vcpkg'
    archive_root_folder_name = 'vcpkg-2025.10.17'
    renamed_archive_dir_path = f'{workspace_dir}/vcpkg/vcpkg-triplets'
    

    if os.path.exists(files_output_path):
        log.info("Previous vcpkg download exists. Deleting...")
        commons.delete_dir(files_output_path)

    log.info("Downloading vcpkg triples...")
    urllib.request.urlretrieve(link, downloaded_archive_path)
    log.info("vcpkg triples downloaded.")

    log.info("Unpacking vcpkg triples...")
    with zipfile.ZipFile(downloaded_archive_path, 'r') as zip_file:
        for file in zip_file.filelist:
            if file.is_dir():
                continue
            output_path = f'{renamed_archive_dir_path}/{file.filename[len(archive_root_folder_name) + 1:]}'
            output_path = os.path.dirname(output_path)
            file.filename = os.path.basename(file.filename)
            zip_file.extract(file, output_path)
    log.info("vcpkg triples unpacked")

def _get_triplets_path(workspace_dir: str) -> str:
    return _vcpkg_2025_10_17_get_triplets_path(workspace_dir)

def _get_buildtrees_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg/buildtrees/'

def _get_packages_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg/packages/'

def _get_install_dir(workspace_dir: str) -> str:
    return f'{workspace_dir}/vcpkg/install/'

def _get_cmake_configs_dir(workspace_dir: str) -> str:
    return f'{_get_install_dir(workspace_dir)}/x64-{platform.system().lower()}/share/'

def is_vcpkg_systemwide_installed() -> bool:
    return shutil.which("vcpkg") is not None

def is_vcpkg_in_workspace_toolset(workspace_dir: str) -> bool:
    exe_present = os.path.exists(_vcpkg_2025_11_19_get_exec_path(workspace_dir))
    triplets_present = os.path.exists(_vcpkg_2025_10_17_get_triplets_path(workspace_dir))
    return exe_present and triplets_present

def get_toolset_vcpkg_exe_path(workspace_dir: str) -> str:
    return _vcpkg_2025_11_19_get_exec_path(workspace_dir)

def download_vcpkg(workspace_dir: str):
    _vcpkg_2025_10_17_triplets_download(workspace_dir)
    return _vcpkg_2025_11_19_exec_download(workspace_dir)

def try_to_find_dependencies(config: config.BuildToolsConfig) -> list[str]:
    json_path = f'{config.project_dir}/vcpkg.json'
    with open(json_path, "r", encoding="UTF-8") as file:
        json_string = file.read()
    deps_json = json.loads(json_string)

    json_deps_array: list[dict] = deps_json['dependencies']
    if type(json_deps_array) != list:
        _error_log_and_die("vcpkg.json have invalid format. 'dependencies' must be an list of dicts")
    
    deps_to_look_for: set[str] = set()
    for json_dep in json_deps_array:
        if type(json_dep) != dict:
            _error_log_and_die("vcpkg.json have invalid format. 'dependencies' must be an list of dicts")
        json_dep_name = json_dep['name']
        if json_dep_name == None:
            _error_log_and_die("vcpkg.json have invalid format. 'dependencies/name' must be present and type str")
        deps_to_look_for.add(json_dep_name)

    vcpkg_deps_dir = _get_cmake_configs_dir(config.workspace_dir)
    def _find_deps() -> set[str]:
        deps_found: set[str] = set()
        for dependency_folder in os.listdir(vcpkg_deps_dir):
            if dependency_folder in deps_to_look_for:
                deps_found.add(commons.realpath(f"{vcpkg_deps_dir}/{dependency_folder}/"))
                deps_to_look_for.remove(dependency_folder)
        return deps_found
    return list(_find_deps())


def download_dependencies(config: config.BuildToolsConfig):
    if config.vcpkg_exe is None: log.error("vcpkg.download_dependencies(): config.vcpkg_exe must be set"); exit(-1)

    os.makedirs(_get_install_dir(config.workspace_dir), exist_ok=True)
    os.makedirs(_get_buildtrees_dir(config.workspace_dir), exist_ok=True)
    os.makedirs(_get_packages_dir(config.workspace_dir), exist_ok=True)

    env = os.environ.copy()
    env['VCPKG_ROOT'] = _get_triplets_path(config.workspace_dir)

    commons.execute_process([
        config.vcpkg_exe, "install", 
        "--x-install-root", _get_install_dir(config.workspace_dir),
        "--x-buildtrees-root", _get_buildtrees_dir(config.workspace_dir),
        "--x-packages-root", _get_packages_dir(config.workspace_dir),
        "--clean-downloads-after-build",
        "--clean-buildtrees-after-build",
        "--clean-after-build",
        "--clean-packages-after-build"
    ], config.project_dir, env)
