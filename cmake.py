import os
import tarfile
import urllib.request
import zipfile
import commons
import shutil
import conan
import vcpkg
from package_manager import PackageManager
import dataclasses
import log
import platform

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



@dataclasses.dataclass
class CMakeConfig:
    cmake_exe: str
    cmake_list_dir: str
    cmake_build_folder: str

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
    if commons.is_windows():
        shutil.move(extracted_path, unified_extracted_path)
    else:
        commons.execute_command(f"mv {extracted_path} {unified_extracted_path}", cwd=extract_path)
    log.info("Renamed cmake folder.")

    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{unified_extracted_path}/bin/cmake{exe_ext}'




def get_config_files_path(config: CMakeConfig, mode: str) -> str:
    return f"{config.cmake_build_folder}/{mode}"

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
    mode: str, 
    workspace_dir: str
):
    log.info(f"Configuring project for '{mode}'")

    os.makedirs(config.cmake_build_folder, exist_ok=True)
    command = [
        config.cmake_exe,
        f"-B", get_config_files_path(config, mode),
        f"-S", config.cmake_list_dir,
        f"-DCMAKE_BUILD_TYPE={mode.capitalize()}"
    ]

    #if package_manager == PackageManager.CONAN or package_manager == PackageManager.ALL:
    command.append(f'-DCMAKE_TOOLCHAIN_FILE={conan.get_toolchain_filepath(mode, workspace_dir)}')
        
    # elif package_manager == PackageManager.VCPKG and package_manager != PackageManager.ALL:
    #     if vcpkg_exe is None:
    #         raise Exception("configure() if vcpkg set as package manager path must be set")
    #     command.append(f'-DCMAKE_TOOLCHAIN_FILE={vcpkg.get_toolchain_path(vcpkg_exe)}')
    # elif package_manager == PackageManager.ALL:
    #     if vcpkg_exe is None:
    #         raise Exception("configure(): vcpkg_exe has to be set in order to find dependencies when 'all' is set")
    #     prefix_paths = vcpkg.find_dependencies_cmakes(vcpkg_exe, project_dir, workspace_dir)
    #     prefix_path = os.pathsep.join(prefix_paths).replace('"', '\\"')
    #     if len(prefix_path) > 0:
    #         command.append(f"-DCMAKE_PREFIX_PATH={prefix_path}")
            
    # if generator is not None:
    #     command.append(f"-G {generator}")

    commons.execute_process(command, config.cmake_build_folder)

def build_project(config: CMakeConfig, mode: str):
    log.info(f"Building project for '{mode}'")

    os.makedirs(config.cmake_build_folder, exist_ok=True)
    command = [
        config.cmake_exe,
        "--build", ".",
        "--config", mode.capitalize(),
    ]
    commons.execute_process(command, get_config_files_path(config, mode))

def delete_cache(config: CMakeConfig, mode: str):
    log.info(f"Deleting project cache for '{mode}'")
    if os.path.exists(get_config_files_path(config, mode)):
        shutil.rmtree(get_config_files_path(config, mode))