import configparser
import os
import zipfile
import commons
import platform
import shutil
import urllib.request
import log
import tarfile

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

def _execute_command(command: str, project_dir: str, workspace_dir: str):
    env = os.environ.copy()
    env['CONAN_HOME'] = _get_conan_home(workspace_dir)
    commons.execute_command(command, project_dir, env)

def download_conan(workspace_dir: str) -> str:
    return _conan_2_23_0_download(workspace_dir)

def is_conan_systemwide_installed() -> bool:
    return shutil.which("conan") != None

def is_conan_in_workspace_toolset(workspace_dir: str) -> bool:
    return os.path.exists(_conan_2_23_0_get_exec_path(workspace_dir))

def get_toolset_conan_exe_path(workspace_dir: str) -> str:
    return _conan_2_23_0_get_exec_path(workspace_dir)

def get_toolchain_filepath(mode: str, workspace_dir: str) -> str:
    file_path = f'{_get_conan_dependencies_path(workspace_dir)}/{mode.lower()}/build/'
    if not commons.is_windows():
        file_path += f'{mode.capitalize()}/'
    return f'{file_path}/generators/conan_toolchain.cmake'

def create_profiles(conan_executable: str, project_dir: str, workspace_dir: str):
    _execute_command(f"{conan_executable} profile detect --force", project_dir, workspace_dir)

    conan_profiles_path = _get_conan_profiles_path(workspace_dir)
    config = configparser.ConfigParser()
    config.read(f'{conan_profiles_path}/default')

    config['settings']['build_type'] = "Release"
    config['settings']['compiler.cppstd'] = "23"

    with open(f'{conan_profiles_path}/release', "w") as file:
        config.write(file)

    config['settings']['build_type'] = "Debug"
    with open(f'{conan_profiles_path}/debug', "w", encoding="UTF-8") as file:
        config.write(file)

def download_dependencies(conan_executable: str, mode: str, project_dir: str, workspace_dir: str):
    _execute_command(' '.join([
        conan_executable,
        'install',
        '.',
        '--build=missing',
        f'--profile={mode.lower()}',
        f'--output-folder={_get_conan_dependencies_path(workspace_dir)}/{mode.lower()}'
    ]), project_dir, workspace_dir)
