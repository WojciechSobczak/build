import configparser
import os
import zipfile
import commons
import platform
import shutil
import urllib.request
import log
import tarfile

_CONAN_EXE: str = ""

def _get_conan_home(workspace_dir: str):
    return f'{workspace_dir}/conan2'

def _get_conan_profiles_path(workspace_dir: str):
    return f'{_get_conan_home(workspace_dir)}/profiles'

def _get_conan_dependencies_path(workspace_dir: str):
    return f'{workspace_dir}/dependencies/conan'

def set_conan_exe(conan_exe: str):
    global _CONAN_EXE
    _CONAN_EXE = conan_exe

def _execute_command(command: str, project_dir: str, workspace_dir: str):
    env = os.environ.copy()
    env['CONAN_HOME'] = _get_conan_home(workspace_dir)
    commons.execute_command(command, project_dir, env)


def is_conan_in_path() -> bool:
    return shutil.which("conan") != None


def download_conan(base_path: str, workspace_dir_name: str) -> str:
    conan_exec_folder = f"{base_path}/{workspace_dir_name}/conan_exec"

    if platform.system() == "Windows":  
        conan_arch_dest = f"{conan_exec_folder}/conan.zip"
        conan_exe_file = f"{conan_exec_folder}/conan.exe"
        download_link = "https://github.com/conan-io/conan/releases/download/2.15.0/conan-2.15.0-windows-x86_64.zip"
    else:
        conan_arch_dest = f"{conan_exec_folder}/conan.tgz"
        conan_exe_file = f"{conan_exec_folder}/bin/conan"
        download_link = "https://github.com/conan-io/conan/releases/download/2.15.0/conan-2.15.0-linux-x86_64.tgz"

    if os.path.exists(conan_exe_file):
        return conan_exe_file

    os.makedirs(os.path.dirname(conan_arch_dest), exist_ok=True)

    log.log("Downloading conan...")
    urllib.request.urlretrieve(download_link, conan_arch_dest)
    if platform.system() == "Windows":  
        with zipfile.ZipFile(conan_arch_dest, 'r') as zip_file:
            zip_file.extractall(conan_exec_folder)
    else:
        with tarfile.open(conan_arch_dest, 'r:gz') as tar_file:
            tar_file.extractall(conan_exec_folder)
    log.log("Conan downloaded")
    os.remove(conan_arch_dest)
    return conan_exe_file


def get_toolchain_filepath(mode: str, workspace_dir: str):
    file_path = f'{_get_conan_dependencies_path(workspace_dir)}/{mode.lower()}/build/'
    if platform.system() != "Windows":
        file_path += f'{mode.capitalize()}/'
    return f'{file_path}/generators/conan_toolchain.cmake'


def create_profiles(project_dir: str, workspace_dir: str):
    _execute_command(f"{_CONAN_EXE} profile detect --force", project_dir, workspace_dir)

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


def install_dependencies(mode: str, project_dir: str, workspace_dir: str):
    _execute_command(' '.join([
        _CONAN_EXE,
        'install',
        '.',
        '--build=missing',
        f'--profile={mode.lower()}',
        f'--output-folder={_get_conan_dependencies_path(workspace_dir)}/{mode.lower()}'
    ]), project_dir, workspace_dir)
