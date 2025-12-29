import os
import tarfile
import urllib.request
import zipfile
import shutil
import platform

from . import commons
from . import log
from . import conan

"""
CMake default structure for this configuration looks like this:

For 4.2.0
WORKSPACE_DIR/cmake:
    - cmake-4.2.0/bin
    - cmake/cmake-4.2.0/bin/ccmake
    - cmake/cmake-4.2.0/bin/cmake
    - cmake/cmake-4.2.0/bin/cmake-gui
    - cmake/cmake-4.2.0/bin/cpack
    - cmake/cmake-4.2.0/bin/ctest
    - <OTHER STUFF THAT IS STRIPPED BY DEFAULT>
"""


class CMakeConfig:
    def __init__(self, 
        cmake_exe: str,
        cmake_list_dir: str,
        cmake_build_folder: str,
        cmake_build_type: str
    ):
        self.cmake_exe = cmake_exe
        self.cmake_list_dir = cmake_list_dir
        self.cmake_build_folder = cmake_build_folder
        
        def _detect_mode():
            match cmake_build_type.lower():
                case "debug": return "Debug"
                case "release": return "Release"
                case "relwithdebinfo": return "RelWithDebInfo" 
                case "minsizerel": return "MinSizeRel"
            log.info(f"Unusual cmake build type detected: '{cmake_build_type}'. Passing it trough as defined.")
            return cmake_build_type
        self.cmake_build_mode = _detect_mode()


def _cmake_4_2_0_get_exec_path(workspace_dir: str) -> str:
    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{workspace_dir}/cmake/cmake-4.2.0/bin/cmake{exe_ext}'

def _cmake_4_2_0_download(workspace_dir: str) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.error(f"Unsupported system: {platform.system()}")
        exit(-1)

    system_string = "windows" if commons.is_windows() else "linux"
    archive_ext = "zip" if commons.is_windows() else "tar.gz"

    link = f"https://github.com/Kitware/CMake/releases/download/v4.2.0/cmake-4.2.0-{system_string}-x86_64.{archive_ext}"
    
    extract_path = f'{workspace_dir}/cmake'
    extracted_path = f'{workspace_dir}/cmake/cmake-4.2.0-{system_string}-x86_64'
    unified_extracted_path = f'{extract_path}/cmake-4.2.0'
    archive_path = f'{workspace_dir}/cmake-4.2.0.{archive_ext}'

    if os.path.exists(unified_extracted_path):
        log.info("Previous cmake download exists. Deleting...")
        commons.delete_dir(unified_extracted_path)

    log.info("Downloading cmake executable...")
    urllib.request.urlretrieve(link, archive_path)
    log.info("CMake downloaded.")

    log.info("Unpacking cmake executable (it can take a minute)...")
    if commons.is_windows():
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            zip_file.extractall(extract_path)
    else:
        # Tarfile on linux is horribly slow, so to speed things up
        # i try to use native tar
        os.makedirs(extract_path, exist_ok=True)
        log.info("Trying with native tar...")
        if shutil.which("tar") != None:
            log.info("tar found. Using tar...")
            commons.execute_command(f"tar -xvzf {archive_path} -C {extract_path}", cwd=extract_path)
        else:
            log.info("tar not found. Using python tarfile...")
            with tarfile.open(archive_path, 'r:gz') as tar_file:
                tar_file.extractall(extract_path)
    log.info("Unpacked cmake folder.")


    log.info("Renaming cmake unpacked folder...")
    commons.rename_dir(extracted_path, unified_extracted_path)
    log.info("Renamed cmake folder.")

    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{unified_extracted_path}/bin/cmake{exe_ext}'

def get_config_files_path(config: CMakeConfig) -> str:
    return f"{config.cmake_build_folder}/{config.cmake_build_mode}"

def download_cmake(workspace_dir: str) -> str:
    return _cmake_4_2_0_download(workspace_dir)

def is_cmake_systemwide_installed() -> bool:
    return shutil.which("cmake") != None

def is_cmake_in_workspace_toolset(workspace_dir: str) -> bool:
    return os.path.exists(_cmake_4_2_0_get_exec_path(workspace_dir))

def get_toolset_cmake_exe_path(workspace_dir: str) -> str:
    return _cmake_4_2_0_get_exec_path(workspace_dir)

def configure(
    config: CMakeConfig,
    workspace_dir: str,
    ninja_exe: str | None = None,
    vcpkg_dependencies: list[str] | None = None
):
    log.info(f"Configuring project for '{config.cmake_build_mode}'")
    os.makedirs(config.cmake_build_folder, exist_ok=True)
    command = [
        config.cmake_exe,
        f'-B', get_config_files_path(config),
        f'-S', config.cmake_list_dir,
        f'-DCMAKE_BUILD_TYPE={config.cmake_build_mode}',
        f'-DCMAKE_TOOLCHAIN_FILE={conan.get_toolchain_filepath(config.cmake_build_mode, workspace_dir, ninja_exe != None)}'
    ]

    if vcpkg_dependencies != None and len(vcpkg_dependencies) > 0:
        command += [
            f'-DCMAKE_PREFIX_PATH={os.pathsep.join(vcpkg_dependencies)}'
        ]

    if ninja_exe != None:
        command += [
            f'-DCMAKE_GENERATOR=Ninja',
            f'-DCMAKE_MAKE_PROGRAM={ninja_exe}',
        ]

    commons.execute_process(command, config.cmake_build_folder)

def build_project(config: CMakeConfig):
    log.info(f"Building project for '{config.cmake_build_mode}'")

    os.makedirs(config.cmake_build_folder, exist_ok=True)
    command = [
        config.cmake_exe,
        "--build", ".",
        "--config", config.cmake_build_mode
    ]
    commons.execute_process(command, get_config_files_path(config))

def delete_cache(config: CMakeConfig):
    log.info(f"Deleting project cache for '{config.cmake_build_mode}'")
    path = get_config_files_path(config)
    if os.path.exists(path):
        commons.delete_dir(path)