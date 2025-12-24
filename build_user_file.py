# This is you do you file and it is intended to give head start
# and be edited as your project need
# It will give you basic usage and is intended to be used as build script 
# for the project and be part of the repository
# It should be downloaded by setup.py script from build_tools repo, but use
# it as you like
# HF

import os
import sys
WORKSPACE_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/.workspace'
sys.path.append(WORKSPACE_DIR)
PROJECT_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/'
import build_tools
import argparse

import platform
PROJECT_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/tests/conan_build_test_dir/'
WORKSPACE_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/.workspace/{platform.system()}/'

def setup_toolset():
    if not build_tools.cmake.is_cmake_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.cmake.download_cmake(WORKSPACE_DIR)
    if not build_tools.conan.is_conan_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.conan.download_conan(WORKSPACE_DIR)
    if not build_tools.vcpkg.is_vcpkg_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.vcpkg.download_vcpkg(WORKSPACE_DIR)
    if not build_tools.ninja.is_ninja_in_workspace_toolset(WORKSPACE_DIR):
        build_tools.ninja.download_ninja(WORKSPACE_DIR)

def main():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    setup_toolset()

    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-c', '--config', default=False, action='store_true', help="Build cmake config.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="debug", help="CMake build mode.")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    parser.add_argument('-s', '--setup-toolset', default=False, action='store_true', help="Setup toolset.")
    args = parser.parse_args()

    cmake_exe = build_tools.cmake.get_toolset_cmake_exe_path(WORKSPACE_DIR)
    ninja_exe = build_tools.ninja.get_toolset_ninja_exe_path(WORKSPACE_DIR)
    if args.dependencies:
        conan_exe = build_tools.conan.get_toolset_conan_exe_path(WORKSPACE_DIR)
        build_tools.conan.create_profiles(conan_exe, cmake_exe, PROJECT_DIR, WORKSPACE_DIR, True)
        build_tools.conan.download_dependencies(conan_exe, args.mode, PROJECT_DIR, WORKSPACE_DIR, ninja_exe)

        vcpkg_exe = build_tools.vcpkg.get_toolset_vcpkg_exe_path(WORKSPACE_DIR)
        build_tools.vcpkg.download_dependencies(vcpkg_exe, WORKSPACE_DIR, PROJECT_DIR)

    cmake_config = build_tools.cmake.CMakeConfig(
        cmake_exe = cmake_exe,
        cmake_build_folder = f'{WORKSPACE_DIR}/cmake/build',
        cmake_list_dir = f'{PROJECT_DIR}'
    )
        
    if args.rebuild:
        build_tools.cmake.delete_cache(cmake_config, args.mode)
    
    if args.config or args.rebuild:
        build_tools.cmake.configure(
            config = cmake_config,
            workspace_dir = WORKSPACE_DIR,
            mode = args.mode,
            ninja_exe = ninja_exe
        )

    if args.build or args.rebuild:
        build_tools.cmake.build_project(cmake_config, args.mode)

if __name__ == "__main__":
    main()



