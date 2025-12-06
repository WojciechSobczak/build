# This is you do you file and it is intended to give head start
# and be edited as your project need
# It will give you basic usage and is intended to be used as build script 
# for the project and be part of the repository
# It should be downloaded by setup.py script from build_tools repo, but use
# it as you like
# HF

import sys, os
WORKSPACE_DIR = f'{os.path.dirname(os.path.realpath(__file__))}/.workspace'
sys.path.append(WORKSPACE_DIR)
import build_tools

import argparse

def setup_tools():
    if not build_tools.cmake.is_cmake_systemwide_installed():
        if not build_tools.cmake.is_cmake_in_workspace_toolset(WORKSPACE_DIR):
            build_tools.cmake.download_cmake(WORKSPACE_DIR)
    

def main():
    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-c', '--cmake-config', default=False, action='store_true', help="Build cmake config.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="debug", help="CMake build mode.")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    parser.add_argument('-s', '--setup-tools', default=False, action='store_true', help="Setup toolset.")


    #

    pass

if __name__ == "__main__":
    main()



