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
    cmake_list_path: str
    cmake_build_folder: str

def _cmake_4_2_0_get_exec_path(workspace_dir: str):
    exe_ext = ".exe" if commons.is_windows() else ""
    return f'{workspace_dir}/cmake/cmake-4.2.0/bin/cmake{exe_ext}'

def _cmake_4_2_0_download(workspace_dir: str, strip: bool = True) -> str:
    if not commons.is_windows() and not commons.is_linux():
        log.log(f"Unsupported system: {platform.system()}")
        exit(-1)

    system_string = "windows" if commons.is_windows() else "linux"
    archive_ext = "zip" if commons.is_windows() else "tar.gz"

    link = f"https://github.com/Kitware/CMake/releases/download/v4.2.0/cmake-4.2.0-{system_string}-x86_64.{archive_ext}"
    
    extract_path = f'{workspace_dir}/cmake'
    extracted_path = f'{workspace_dir}/cmake/cmake-4.2.0-{system_string}-x86_64'
    unified_extracted_path = f'{extract_path}/cmake-4.2.0'

    root_zip_folder_name = f'cmake-4.2.0-{system_string}-x86_64'
    archive_path = f'{workspace_dir}/cmake-4.2.0.{archive_ext}'

    urllib.request.urlretrieve(link, archive_path)

    if commons.is_windows():
        with zipfile.ZipFile(archive_path, 'r') as zip_file:
            if strip == False:
                zip_file.extractall(extract_path)
            else:
                files_to_extract = [file for file in zip_file.filelist if file.filename.startswith(f'{root_zip_folder_name}/bin')]
                for file in files_to_extract:
                    zip_file.extract(file, extract_path)
        shutil.move(extracted_path, unified_extracted_path)
        return f'{unified_extracted_path}/bin/cmake.exe'

    if commons.is_linux():
        with tarfile.open(archive_path, 'r:gz') as tar_file:
            if strip == False:
                tar_file.extractall(extract_path)
            else:
                files_to_extract = [file for file in tar_file.getmembers() if file.path.startswith(f'{root_zip_folder_name}/bin')]
                for file in files_to_extract:
                    tar_file.extract(file, extract_path)
        shutil.move(extracted_path, unified_extracted_path)
        return f'{unified_extracted_path}/bin/cmake'

def get_config_files_path(config: CMakeConfig, mode: str):
    return f"{config.cmake_build_folder}/{mode}"

def download_cmake(workspace_dir: str, strip: bool = True) -> str:
    return _cmake_4_2_0_download(workspace_dir, strip)

def is_cmake_systemwide_installed():
    return shutil.which("cmake") != None

def is_cmake_in_workspace_toolset(workspace_dir: str):
    return os.path.exists(_cmake_4_2_0_get_exec_path(workspace_dir))


def configure(
    config: CMakeConfig,
    mode: str, 
    package_manager: PackageManager, 
    workspace_dir: str,
    project_dir: str,
    vcpkg_exe: str | None,
    generator: str | None
):
    os.makedirs(config.cmake_build_folder, exist_ok=True)

    command = [
        config.cmake_exe,
        f"-B", get_config_files_path(mode),
        f"-S", config.cmake_list_path,
        f"-DCMAKE_BUILD_TYPE={mode.capitalize()}"
    ]

    if package_manager == PackageManager.CONAN or package_manager == PackageManager.ALL:
        command.append(f'-DCMAKE_TOOLCHAIN_FILE={conan.get_toolchain_filepath(mode, workspace_dir)}')
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

    commons.execute_process(command, config.cmake_list_path)

def build_project(config: CMakeConfig, mode: str):
    os.makedirs(config.cmake_build_folder, exist_ok=True)
    command = [
        config.cmake_exe,
        "--build", ".",
        "--config", mode.capitalize(),
    ]
    commons.execute_process(command, get_config_files_path(config))

def delete_cache(mode: str):
    if os.path.exists(get_config_files_path(mode)):
        shutil.rmtree(get_config_files_path(mode))