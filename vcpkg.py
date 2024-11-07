import commons

_VCPKG_EXE: str = ""
_VCPKG_BASE_PATH: str = ""
_VCPKG_DEPENDENCIES_FOLDER: str = ""


def setup_paths(vcpkg_exe: str, base_path: str):
    global _VCPKG_EXE
    global _VCPKG_BASE_PATH
    global _VCPKG_DEPENDENCIES_FOLDER
    
    _VCPKG_EXE = vcpkg_exe
    _VCPKG_BASE_PATH = commons.realpath(base_path)
    _VCPKG_DEPENDENCIES_FOLDER = f'{_VCPKG_BASE_PATH}/.dependencies'

def _execute_process(command: list[str]):
    commons.execute_process(command, _VCPKG_BASE_PATH)

def install_dependencies():
    _execute_process([
        _VCPKG_EXE, "install", 
        "--x-install-root", _VCPKG_DEPENDENCIES_FOLDER,
        "--x-buildtrees-root", _VCPKG_DEPENDENCIES_FOLDER,
        "--downloads-root", _VCPKG_DEPENDENCIES_FOLDER,
        "--x-packages-root", _VCPKG_DEPENDENCIES_FOLDER,
    ])