import os
import commons
import shutil
import conan
import vcpkg
from package_manager import PackageManager

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
    

def configure(
    config: str, 
    package_manager: PackageManager, 
    workspace_dir: str,
    project_dir: str,
    vcpkg_exe: str | None,
    generator: str | None
):
    os.makedirs(_CMAKE_BUILD_FOLDER, exist_ok=True)

    command = [
        _CMAKE_EXE,
        f"-B", get_config_files_path(config),
        f"-S", _CMAKE_LIST_PATH,
        f"-DCMAKE_BUILD_TYPE={config.capitalize()}",
        
    ]

    if package_manager == PackageManager.CONAN or package_manager == PackageManager.ALL:
        command.append(f'-DCMAKE_TOOLCHAIN_FILE={conan.get_toolchain_filepath(config, workspace_dir)}')
    elif package_manager == PackageManager.VCPKG and package_manager != PackageManager.ALL:
        if vcpkg_exe is None:
            raise Exception("configure() if vcpkg set as package manager path must be set")
        command.append(f'-DCMAKE_TOOLCHAIN_FILE={vcpkg.get_toolchain_path(vcpkg_exe)}')
    elif package_manager == PackageManager.ALL:
        if vcpkg_exe is None:
            raise Exception("configure(): vcpkg_exe has to be set in order to find dependencies when 'all' is set")
        prefix_paths = vcpkg.find_dependencies_cmakes(vcpkg_exe, project_dir, workspace_dir)
        prefix_path = os.pathsep.join(prefix_paths).replace('"', '\\"')
        if len(prefix_path) > 0:
            command.append(f"-DCMAKE_PREFIX_PATH={prefix_path}")
            print(f"PATHS: {prefix_path}")
            
    if generator is not None:
        command.append(f"-G {generator}")

    commons.execute_process(command, _CMAKE_LIST_PATH)

def build_project(config: str):
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