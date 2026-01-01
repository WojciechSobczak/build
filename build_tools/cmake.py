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
        build_type: str,
        prefix_paths: list[str] | None = None
    ):
        self.list_dir = list_dir
        self.build_dir = build_dir
        self.prefix_paths = [] if prefix_paths is None else prefix_paths
        
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

    archive_root_folder_name = f'cmake-4.2.0-{system_string}-x86_64'
    renamed_archive_dir_name = f'cmake-4.2.0'
    renamed_archive_dir_path = f'{cmake_main_dir}/{renamed_archive_dir_name}'
    downloaded_archive_path = f'{workspace_dir}/cmake-4.2.0.{archive_ext}'

    if os.path.exists(renamed_archive_dir_path):
        log.info("Previous cmake download exists. Deleting...")
        commons.delete_dir(renamed_archive_dir_path)

    log.info("Downloading cmake executable...")
    urllib.request.urlretrieve(download_link, downloaded_archive_path)
    log.info("CMake downloaded.")

    exe_ext = ".exe" if commons.is_windows() else ""
    package_dirs_exclusion_list: list[str] = [
        f'{archive_root_folder_name}/doc',
        f'{archive_root_folder_name}/man',
        f'{archive_root_folder_name}/share/aclocal',
        f'{archive_root_folder_name}/share/bash-completion',
        f'{archive_root_folder_name}/share/cmake-4.2/Help',
        f'{archive_root_folder_name}/share/cmake-4.2/Licenses',
        f'{archive_root_folder_name}/share/emacs',
        f'{archive_root_folder_name}/share/vim',
        f'{archive_root_folder_name}/share/icons', # Additionally in linux package
        f'{archive_root_folder_name}/share/mime',  # Additionally in linux package
    ]
    package_files_exclusion_list: list[str] = [
        f'{archive_root_folder_name}/bin/cmake-gui{exe_ext}',
        f'{archive_root_folder_name}/bin/cmcldeps{exe_ext}',
        f'{archive_root_folder_name}/bin/cpack{exe_ext}',
        f'{archive_root_folder_name}/bin/ctest{exe_ext}',
    ]

    def _is_excluded(filename: str) -> bool:
        for excluded_dir in package_dirs_exclusion_list:
            if filename.startswith(excluded_dir):
                return True
        for excluded_file in package_files_exclusion_list:
            if filename == excluded_file:
                return True
        return False
    
    log.info("Unpacking cmake executable (it can take a minute)...")
    os.makedirs(cmake_main_dir, exist_ok=True)
    if commons.is_windows():
        with zipfile.ZipFile(downloaded_archive_path, 'r') as zip_file:
            for file in zip_file.filelist:
                if _is_excluded(file.filename) or file.is_dir(): 
                    continue
                output_path = f'{renamed_archive_dir_path}/{file.filename[len(archive_root_folder_name) + 1:]}'
                output_path = os.path.dirname(output_path)
                file.filename = os.path.basename(file.filename)
                zip_file.extract(file, output_path)
    else:
        with tarfile.open(downloaded_archive_path, 'r:gz') as tar_file:
            for file_path, file_member in zip(tar_file.getnames(), tar_file.getmembers()):
                if _is_excluded(file_path) or file_member.isdir(): 
                    continue
                output_path = f'{renamed_archive_dir_path}/{file_path[len(archive_root_folder_name) + 1:]}'
                output_path = os.path.dirname(output_path)
                file_member.name = f'{output_path}/{os.path.basename(file_path)}'
                tar_file.extract(file_member, output_path)

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

    prefix_paths = config.prefix_paths
    if toolset_config.is_vcpkg_set() and vcpkg_dependencies is not None and len(vcpkg_dependencies) > 0:
        prefix_paths += vcpkg_dependencies
    
    if len(prefix_paths) > 0:
        command += [
            f'-DCMAKE_PREFIX_PATH={';'.join(prefix_paths)}'
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