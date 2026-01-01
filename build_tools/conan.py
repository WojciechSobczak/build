import configparser
import os
import zipfile
import platform
import shutil
import urllib.request
import tarfile

from . import log
from . import commons
from . import config

"""
conan default structure for this configuration looks like this:

For 2.23.0
WINDOWS:
    WORKSPACE_DIR/conan:
        - conan2_home
        - _internal
        - conan.exe
LINUX:
    WORKSPACE_DIR/conan:
        - conan2_home
        - bin/
            - internal
            - conan
"""

def _conan_2_23_0_get_exec_path(workspace_dir: str) -> str:
    if commons.is_windows():
        return f'{workspace_dir}/conan/conan.exe'
    else:
        return f'{workspace_dir}/conan/bin/conan'

def _conan_2_23_0_download(workspace_dir: str) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.info(f"Unsupported system: {platform.system()}")
        exit(-1)

    system_string = "windows" if commons.is_windows() else "linux"
    archive_ext = "zip" if commons.is_windows() else "tgz"
    link = f"https://github.com/conan-io/conan/releases/download/2.23.0/conan-2.23.0-{system_string}-x86_64.{archive_ext}"
    extract_path = f'{workspace_dir}/conan'
    archive_path = f'{workspace_dir}/conan-2.23.0.{archive_ext}'

    if os.path.exists(extract_path):
        log.info("Previous conan download exists. Deleting...")
        commons.delete_dir(extract_path)

    log.info("Downloading conan...")
    urllib.request.urlretrieve(link, archive_path)
    log.info("Conan downloaded")

    log.info("Unpacking conan...")
    if platform.system() == "Windows":  
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            zip_file.extractall(extract_path)
    else:
        with tarfile.open(archive_path, 'r:gz') as tar_file:
            tar_file.extractall(extract_path)

    log.info("Conan unpacked")
    return f'{extract_path}'

def _get_conan_home(workspace_dir: str) -> str:
    return f'{workspace_dir}/conan2_home'

def _get_conan_profiles_path(workspace_dir: str) -> str:
    return f'{_get_conan_home(workspace_dir)}/profiles'

def _get_conan_dependencies_path(workspace_dir: str) -> str:
    return f'{_get_conan_home(workspace_dir)}/dependencies'

def _execute_process(command: list[str], project_dir: str, workspace_dir: str, ninja_exe: str | None = None):
    env = os.environ.copy()
    env['CONAN_HOME'] = _get_conan_home(workspace_dir)
    if ninja_exe is not None:
        # Value of type variable "AnyOrLiteralStr" of "dirname" cannot be "str | None". REASON: But it can actually.
        env['PATH'] = os.path.dirname(ninja_exe) + os.pathsep + env['PATH'] # type: ignore
    commons.execute_process(command, project_dir, env)

def download_conan(workspace_dir: str) -> str:
    return _conan_2_23_0_download(workspace_dir)

def is_conan_systemwide_installed() -> bool:
    return shutil.which("conan") is not None

def is_conan_in_workspace_toolset(workspace_dir: str) -> bool:
    return os.path.exists(_conan_2_23_0_get_exec_path(workspace_dir))

def get_toolset_conan_exe_path(workspace_dir: str) -> str:
    return _conan_2_23_0_get_exec_path(workspace_dir)

def get_toolchain_filepath(mode: str, workspace_dir: str, ninja_generator: bool = True) -> str:
    file_path = f'{_get_conan_dependencies_path(workspace_dir)}/{mode.lower()}/build'
    if not commons.is_windows() or ninja_generator:
        file_path += f'{mode.capitalize()}/'
    return f'{file_path}/generators/conan_toolchain.cmake'

def create_profiles(config: config.BuildToolsConfig):
    if config.conan_exe is None: log.error("conan.create_profiles(): config.conan_exe must be set"); exit(-1)
    
    _execute_process([f"{config.conan_exe}", "profile", "detect", "--force"], config.project_dir, config.workspace_dir)

    conan_profiles_path = _get_conan_profiles_path(config.workspace_dir)
    
    conan_profile = configparser.ConfigParser()
    conan_profile.read(f'{conan_profiles_path}/default')

    conan_profile['settings']['build_type'] = "Release"
    conan_profile['settings']['compiler.cppstd'] = "23"
    
    conan_profile.add_section('conf')
    conan_profile['conf']['tools.cmake:cmake_program'] = config.cmake_exe
    if config.is_ninja_set():
        conan_profile['conf']['tools.cmake.cmaketoolchain:generator'] = "Ninja"

    with open(f'{conan_profiles_path}/release', "w") as file:
        conan_profile.write(file)

    conan_profile['settings']['build_type'] = "Debug"
    with open(f'{conan_profiles_path}/debug', "w", encoding="UTF-8") as file:
        conan_profile.write(file)

def download_dependencies(config: config.BuildToolsConfig):
    if config.conan_exe is None: log.error("conan.download_dependencies(): config.conan_exe must be set"); exit(-1)

    _execute_process([
        config.conan_exe,
        f'install',
        f'.',
        f'--build', 'missing',
        f'--profile', config.build_mode.lower(),
        f'--output-folder', f'{_get_conan_dependencies_path(config.workspace_dir)}/{config.build_mode.lower()}',
    ], config.project_dir, config.workspace_dir, config.ninja_exe)
