# This is "you do you" file and it is intended to give head start
# and be edited as your project need
# It will give you basic usage and is intended to be used as build script 
# for the project and be part of the repository
# It should be downloaded by setup.py script from build_tools repo, but use
# it as you like
# HF

import os
WORKSPACE_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/.workspace'
PROJECT_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/'

import sys
sys.path.append(WORKSPACE_DIR)
import build_tools
import argparse
import shutil

def setup_toolset() -> tuple[str, str, str | None, str | None]:
    # If you want all tools to be downloaded, or some to be downloaded this is 
    # the fragment you want to mess with. It is default for this script
    if not build_tools.cmake.is_cmake_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.cmake.download_cmake(WORKSPACE_DIR)
    if not build_tools.conan.is_conan_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.conan.download_conan(WORKSPACE_DIR)

    # BE AWARE: With ninja and mscompiler you have to run "vcvarsall.bat x64" before 
    # running the script or have cl.exe and stuff accessible in path
    # as it requires additional setup, it is disabled by default
    if False and not build_tools.ninja.is_ninja_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.ninja.download_ninja(WORKSPACE_DIR)
    # VCPKG is addon that have to used in certain way alongside conan so its disabled by default
    if False and not build_tools.vcpkg.is_vcpkg_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.vcpkg.download_vcpkg(WORKSPACE_DIR)
        
    cmake_exe = build_tools.cmake.get_toolset_cmake_exe_path(WORKSPACE_DIR)
    conan_exe = build_tools.conan.get_toolset_conan_exe_path(WORKSPACE_DIR)
    ninja_exe = None
    vcpkg_exe = None
    if False:
        ninja_exe = build_tools.ninja.get_toolset_ninja_exe_path(WORKSPACE_DIR)
        vcpkg_exe = build_tools.vcpkg.get_toolset_vcpkg_exe_path(WORKSPACE_DIR)

    # If you have all tools in path, just replace it with plain names as here
    # this is disabled by default as it requires environment setup
    if False:
        cmake_exe = shutil.which("cmake")
        ninja_exe = shutil.which("ninja")
        conan_exe = shutil.which("conan")
        vcpkg_exe = shutil.which("vcpkg")

    assert(cmake_exe != None)
    assert(conan_exe != None)

    return (cmake_exe, conan_exe, ninja_exe, vcpkg_exe)

def main():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    cmake_exe, conan_exe, ninja_exe, vcpkg_exe = setup_toolset()

    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-c', '--config', default=False, action='store_true', help="Build cmake config.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="debug", help="Build mode. [debug, release, ...]")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    args = parser.parse_args()
    
    if args.dependencies:
        build_tools.conan.create_profiles(conan_exe, cmake_exe, PROJECT_DIR, WORKSPACE_DIR, ninja_exe != None)
        build_tools.conan.download_dependencies(conan_exe, args.mode, PROJECT_DIR, WORKSPACE_DIR, ninja_exe)
        if vcpkg_exe != None:
            build_tools.vcpkg.download_dependencies(vcpkg_exe, WORKSPACE_DIR, PROJECT_DIR)

    cmake_config = build_tools.cmake.CMakeConfig(
        cmake_exe = cmake_exe,
        cmake_build_folder = f'{WORKSPACE_DIR}/cmake/build',
        cmake_list_dir = f'{PROJECT_DIR}',
        cmake_build_type = args.mode
    )
        
    if args.rebuild:
        build_tools.cmake.delete_cache(cmake_config)
    
    if args.config or args.rebuild:
        vcpkg_dependencies = []
        if vcpkg_exe != None:
            vcpkg_dependencies = build_tools.vcpkg.try_to_find_dependencies(WORKSPACE_DIR, PROJECT_DIR)

        build_tools.cmake.configure(
            config = cmake_config,
            workspace_dir = WORKSPACE_DIR,
            ninja_exe = ninja_exe,
            vcpkg_dependencies = vcpkg_dependencies
        )

    if args.build or args.rebuild:
        build_tools.cmake.build_project(cmake_config)

if __name__ == "__main__":
    main()



