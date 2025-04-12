import configparser
import os
import commons
import platform

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
