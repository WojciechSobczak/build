import configparser
import os
import commons

_CONAN_EXE = None
_CONAN_BASE_PATH = None
_CONAN_HOME = None
_CONAN_PROFILES_PATH = None
_CONAN_DEPENDENCIES_FOLDER = None


def setup_paths(conan_exe: str, base_path: str):
    global _CONAN_EXE
    global _CONAN_BASE_PATH
    global _CONAN_HOME
    global _CONAN_PROFILES_PATH
    global _CONAN_DEPENDENCIES_FOLDER
    
    _CONAN_EXE = conan_exe
    _CONAN_BASE_PATH = commons.realpath(base_path)
    _CONAN_HOME = commons.realpath(f'{_CONAN_BASE_PATH}/.conan2')
    _CONAN_PROFILES_PATH = f'{_CONAN_HOME}/profiles'
    _CONAN_DEPENDENCIES_FOLDER = f'{_CONAN_BASE_PATH}/.dependencies/conan'


def _execute_command(command: str):
    env = os.environ.copy()
    env['CONAN_HOME'] = _CONAN_HOME
    commons.execute_command(command, _CONAN_BASE_PATH, env)


def get_toolchain_filepath(mode: str):
    return f'{_CONAN_DEPENDENCIES_FOLDER}/{mode.lower()}/build/generators/conan_toolchain.cmake'


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
        f'--output-folder=.dependencies/conan/{mode.lower()}'
    ]))
