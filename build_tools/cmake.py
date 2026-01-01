import os
import tarfile
import urllib.request
import zipfile
import shutil
import platform

from . import commons
from . import log
from . import conan
from . import config

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
        list_dir: str,
        build_dir: str,
        build_type: str
    ):
        self.list_dir = list_dir
        self.build_dir = build_dir
        
        def _detect_mode() -> str:
            match build_type.lower():
                case "debug": return "Debug"
                case "release": return "Release"
                case "relwithdebinfo": return "RelWithDebInfo" 
                case "minsizerel": return "MinSizeRel"
            log.info(f"Unusual cmake build type detected: '{build_type}'. Passing it trough as defined.")
            return build_type
        self.build_mode = _detect_mode()


def _cmake_4_2_0_get_exec_path(workspace_dir: str) -> str:
    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{workspace_dir}/cmake/cmake-4.2.0/bin/cmake{exe_ext}'

def _cmake_4_2_0_download(workspace_dir: str) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.error(f"Unsupported system: {platform.system()}")
        exit(-1)

    system_string = "windows" if commons.is_windows() else "linux"
    archive_ext = "zip" if commons.is_windows() else "tar.gz"

    download_link = f"https://github.com/Kitware/CMake/releases/download/v4.2.0/cmake-4.2.0-{system_string}-x86_64.{archive_ext}"
    cmake_main_dir = f'{workspace_dir}/cmake'
    unpacked_archive_dir_path = f'{cmake_main_dir}/cmake-4.2.0-{system_string}-x86_64'
    renamed_archive_dir_name = f'cmake-4.2.0'
    renamed_archive_dir_path = f'{cmake_main_dir}/{renamed_archive_dir_name}'
    downloaded_archive_path = f'{workspace_dir}/cmake-4.2.0.{archive_ext}'

    if os.path.exists(renamed_archive_dir_path):
        log.info("Previous cmake download exists. Deleting...")
        commons.delete_dir(renamed_archive_dir_path)

    log.info("Downloading cmake executable...")
    urllib.request.urlretrieve(download_link, downloaded_archive_path)
    log.info("CMake downloaded.")

    log.info("Unpacking cmake executable (it can take a minute)...")
    if commons.is_windows():
        with zipfile.ZipFile(downloaded_archive_path, 'r') as zip_file:
            zip_file.extractall(cmake_main_dir)
    else:
        # Tarfile on linux is horribly slow, so to speed things up
        # i try to use native tar
        os.makedirs(cmake_main_dir, exist_ok=True)
        log.info("Trying with native tar...")
        if shutil.which("tar") is not None:
            log.info("tar found. Using tar...")
            commons.execute_command(f"tar -xvzf {downloaded_archive_path} -C {cmake_main_dir} > /dev/null", cwd=cmake_main_dir)
        else:
            log.info("tar not found. Using python tarfile...")
            with tarfile.open(downloaded_archive_path, 'r:gz') as tar_file:
                tar_file.extractall(cmake_main_dir)
    log.info("Unpacked cmake folder.")


    log.info("Renaming cmake unpacked folder...")
    commons.rename_dir(unpacked_archive_dir_path, renamed_archive_dir_name)
    log.info("Renamed cmake folder.")

    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{renamed_archive_dir_path}/bin/cmake{exe_ext}'

def get_config_files_path(config: CMakeConfig) -> str:
    return f"{config.build_dir}/{config.build_mode}"

def download_cmake(workspace_dir: str) -> str:
    return _cmake_4_2_0_download(workspace_dir)

def is_cmake_systemwide_installed() -> bool:
    return shutil.which("cmake") is not None

def is_cmake_in_workspace_toolset(workspace_dir: str) -> bool:
    return os.path.exists(_cmake_4_2_0_get_exec_path(workspace_dir))

def get_toolset_cmake_exe_path(workspace_dir: str) -> str:
    return _cmake_4_2_0_get_exec_path(workspace_dir)

def configure(
    config: CMakeConfig,
    toolset_config: config.BuildToolsConfig,
    vcpkg_dependencies: list[str] | None = None
):
    log.info(f"Configuring project for '{config.build_mode}'")
    os.makedirs(config.build_dir, exist_ok=True)
    command = [
        toolset_config.cmake_exe,
        f'-B', get_config_files_path(config),
        f'-S', config.list_dir,
        f'-DCMAKE_BUILD_TYPE={config.build_mode}'
    ]

    if toolset_config.is_conan_set():
        command += [
            f'-DCMAKE_TOOLCHAIN_FILE={conan.get_toolchain_filepath(config.build_mode, toolset_config.workspace_dir, toolset_config.is_ninja_set())}'
        ]

    if toolset_config.is_vcpkg_set() and vcpkg_dependencies is not None and len(vcpkg_dependencies) > 0:
        command += [
            f'-DCMAKE_PREFIX_PATH={';'.join(vcpkg_dependencies)}'
        ]

    if toolset_config.is_ninja_set():
        command += [
            f'-DCMAKE_GENERATOR=Ninja',
            f'-DCMAKE_MAKE_PROGRAM={toolset_config.ninja_exe}',
        ]

    commons.execute_process(command, config.build_dir)

def build_project(config: CMakeConfig, toolset_config: config.BuildToolsConfig):
    log.info(f"Building project for '{config.build_mode}'")

    os.makedirs(config.build_dir, exist_ok=True)
    command = [
        toolset_config.cmake_exe,
        "--build", ".",
        "--config", config.build_mode
    ]
    commons.execute_process(command, get_config_files_path(config))

def delete_cache(config: CMakeConfig):
    log.info(f"Deleting project cache for '{config.build_mode}'")
    path = get_config_files_path(config)
    if os.path.exists(path):
        commons.delete_dir(path)