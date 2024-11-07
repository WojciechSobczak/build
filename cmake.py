import os
import commons
import shutil

_CMAKE_EXE: str = ""
_CMAKE_LIST_PATH: str = ""
_CMAKE_BUILD_FOLDER: str = ""

def setup_paths(cmake_exe: str, base_path: str):
    global _CMAKE_EXE
    global _CMAKE_LIST_PATH
    global _CMAKE_BUILD_FOLDER
    
    _CMAKE_EXE = cmake_exe
    _CMAKE_LIST_PATH = commons.realpath(base_path)
    _CMAKE_BUILD_FOLDER = f'{_CMAKE_LIST_PATH}/.build'

class PackageManager:
    def generate_toolchain_param(self): ...

class ConanPackageManager(PackageManager):
    def __init__(self, conan_toolchain_file: str) -> None:
        self.conan_toolchain_file = conan_toolchain_file

    def generate_toolchain_param(self):
        return self.conan_toolchain_file
    
class VcpkgPackageManager(PackageManager):
    def __init__(self, vcpkg_path: str) -> None:
        self.vcpkg_path = vcpkg_path

    def generate_toolchain_param(self):
        vcpkg_toolchain = commons.normalize_path(os.path.dirname(self.vcpkg_path))
        vcpkg_toolchain += "/scripts/buildsystems/vcpkg.cmake"
        return vcpkg_toolchain


def configure(config: str, package_manager: PackageManager, generator: str):
    os.makedirs(_CMAKE_BUILD_FOLDER, exist_ok=True)
    command = [
        _CMAKE_EXE,
        f"-B", _CMAKE_BUILD_FOLDER,
        f"-S", _CMAKE_LIST_PATH,
        f"-DCMAKE_BUILD_TYPE={config.capitalize()}",
        f'-DCMAKE_TOOLCHAIN_FILE={package_manager.generate_toolchain_param()}'
    ]
    if generator is not None:
        command.append(f"-G {generator}")

    commons.execute_process(command, _CMAKE_LIST_PATH)

def build(config: str):
    os.makedirs(_CMAKE_BUILD_FOLDER, exist_ok=True)
    command = [
        _CMAKE_EXE,
        "--build", ".",
        "--config", config.capitalize(),
    ]
    commons.execute_process(command, _CMAKE_BUILD_FOLDER)

def delete_cache():
    if os.path.exists(_CMAKE_BUILD_FOLDER):
        shutil.rmtree(_CMAKE_BUILD_FOLDER)