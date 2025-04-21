import os
import commons
import shutil

_CMAKE_EXE: str = ""
_CMAKE_LIST_PATH: str = ""
_CMAKE_BUILD_FOLDER: str = ""

def setup_paths(cmake_exe: str, base_path: str, workspace_dir_name: str):
    global _CMAKE_EXE
    global _CMAKE_LIST_PATH
    global _CMAKE_BUILD_FOLDER
    
    _CMAKE_EXE = cmake_exe
    _CMAKE_LIST_PATH = commons.realpath(base_path)
    _CMAKE_BUILD_FOLDER = f'{_CMAKE_LIST_PATH}/{workspace_dir_name}/cmake_build'

def get_config_files_path(mode: str):
    return f"{_CMAKE_BUILD_FOLDER}/{mode}"

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


def configure(config: str, conan_toolchain_path: str, prefix_paths: list[str], generator: str | None):
    os.makedirs(_CMAKE_BUILD_FOLDER, exist_ok=True)

    command = [
        _CMAKE_EXE,
        f"-B", get_config_files_path(config),
        f"-S", _CMAKE_LIST_PATH,
        f"-DCMAKE_BUILD_TYPE={config.capitalize()}",
        f'-DCMAKE_TOOLCHAIN_FILE={conan_toolchain_path}'
    ]
    if generator is not None:
        command.append(f"-G {generator}")

    prefix_path = os.pathsep.join(prefix_paths).replace('"', '\\"')
    if len(prefix_path) > 0:
        command.append(f"-DCMAKE_PREFIX_PATH={prefix_path}")
        print(f"PATHS: {prefix_path}")

    commons.execute_process(command, _CMAKE_LIST_PATH)

def build(config: str):
    os.makedirs(_CMAKE_BUILD_FOLDER, exist_ok=True)
    command = [
        _CMAKE_EXE,
        "--build", ".",
        "--config", config.capitalize(),
    ]
    commons.execute_process(command, get_config_files_path(config))

def delete_cache(config: str):
    if os.path.exists(get_config_files_path(config)):
        shutil.rmtree(get_config_files_path(config))