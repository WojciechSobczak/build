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
_CONAN_BASE_PATH: str = ""
_CONAN_HOME: str = ""
_CONAN_PROFILES_PATH: str = ""
_CONAN_DEPENDENCIES_FOLDER: str = ""
_CONAN_WORKDIR_PATH: str = ""

def setup_paths(conan_exe: str, base_path: str, workspace_dir_name: str):
    global _CONAN_EXE
    global _CONAN_BASE_PATH
    global _CONAN_HOME
    global _CONAN_PROFILES_PATH
    global _CONAN_DEPENDENCIES_FOLDER
    global _CONAN_WORKDIR_PATH
    
    _CONAN_EXE = conan_exe
    _CONAN_WORKDIR_PATH = f"{commons.realpath(base_path)}/"

    _CONAN_BASE_PATH = f"{_CONAN_WORKDIR_PATH}/{workspace_dir_name}"
    _CONAN_HOME = commons.realpath(f'{_CONAN_BASE_PATH}/conan2')
    _CONAN_PROFILES_PATH = f'{_CONAN_HOME}/profiles'
    _CONAN_DEPENDENCIES_FOLDER = f'{_CONAN_BASE_PATH}/dependencies/conan'

def _execute_command(command: str):
    env = os.environ.copy()
    env['CONAN_HOME'] = _CONAN_HOME
    commons.execute_command(command, _CONAN_WORKDIR_PATH, env)


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


def get_toolchain_filepath(mode: str):
    file_path = f'{_CONAN_DEPENDENCIES_FOLDER}/{mode.lower()}/build/'
    if platform.system() != "Windows":
        file_path += f'{mode.capitalize()}/'
    return f'{file_path}/generators/conan_toolchain.cmake'


def create_profiles():
    _execute_command(f"{_CONAN_EXE} profile detect --force")

    config = configparser.ConfigParser()
    config.read(f'{_CONAN_PROFILES_PATH}/default')

    config['settings']['build_type'] = "Release"
    config['settings']['compiler.cppstd'] = "23"

    with open(f'{_CONAN_PROFILES_PATH}/release', "w") as file:
        config.write(file)

    config['settings']['build_type'] = "Debug"
    with open(f'{_CONAN_PROFILES_PATH}/debug', "w", encoding="UTF-8") as file:
        config.write(file)


def install_dependencies(mode: str):
    _execute_command(' '.join([
        _CONAN_EXE,
        'install',
        '.',
        '--build=missing',
        f'--profile={mode.lower()}',
        f'--output-folder={_CONAN_DEPENDENCIES_FOLDER}/{mode.lower()}'
    ]))
