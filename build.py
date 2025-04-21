import dataclasses
import os
import argparse
import shutil
import commons
import conan
import cmake
import vcpkg
import projgen
import sys
import platform



@dataclasses.dataclass
class BuildArgs:
    build: bool
    rebuild: bool
    config: bool
    workdir: str
    mode: str
    conan_path: str
    vcpkg_path: str
    dependencies: bool
    cmake_path: str
    generator: str | None
    generate_project: bool
    generate_config: bool
    clion: bool
    workspace_dir_name: str

    @staticmethod
    def _extract_path(path: str | None) -> str | None:
        if path is None:
            return None
        if ("/" in path or "\\" in path) and os.path.exists(path):
            if not os.path.isfile(path):
                path = None
        if path is not None:
            if shutil.which(path) is None:
                path = None
        return path
    
    @staticmethod
    def _get_absolute_path(path: str | None) -> str | None:
        if path is None:
            return None
        if "/" in path or "\\" in path:
            return commons.realpath(path)
        path = shutil.which(path)
        if path is not None:
            return commons.normalize_path(path)
        return path

    @staticmethod
    def parseArgs(args: argparse.Namespace) -> 'BuildArgs':
        if args.workdir == None:
            args.workdir = os.path.realpath(os.getcwd())
            print(f"[WARNING] 'workdir' not set. Set to default: {args.workdir}]")

        mode: str = args.mode
        mode = mode.lower().strip()
        if mode != "debug" and mode != "release":
            raise Exception("Argparse error: Only 'debug' or 'release' are allowed for mode")

        cmake_path = BuildArgs._extract_path(args.cmake_path)
        if cmake_path is None:
            raise Exception("Argparse error: if cmake is not available in PATH, 'cmake-path' must be set to path to executable")
        cmake_path = BuildArgs._get_absolute_path(args.cmake_path)

        conan_path = BuildArgs._extract_path(args.conan)
        if conan_path is None:
            conan_path = ""

        vcpkg_path = BuildArgs._extract_path(args.vcpkg)
        if vcpkg_path is None:
            vcpkg_path = ""
        
        return BuildArgs(
            build = args.build, 
            rebuild = args.rebuild,
            config = args.cmake_config,
            workdir = commons.realpath(args.workdir),
            mode = mode,
            conan_path = conan_path, # type: ignore
            dependencies = args.dependencies,
            cmake_path = cmake_path, # type: ignore
            vcpkg_path = vcpkg_path,
            generator = args.cmake_generator,
            generate_project = args.generate_project,
            generate_config = args.generate_config,
            clion = args.clion,
            workspace_dir_name = args.workspace_dir_name
        )

def main():
    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-w', '--workdir', help="Script working directory.")
    parser.add_argument('-c', '--cmake-config', default=False, action='store_true', help="Build cmake config.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="debug", help="CMake build mode. Either 'debug' or 'release' (case insensitive).")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    parser.add_argument('--workspace-dir-name', help="Workspace files directory name", default=".workspace")
    parser.add_argument('--clion', help="Generate files for CLion IDE", default=False, action='store_true')
    parser.add_argument('--cmake-path', default="cmake", help="cmake executable path")
    parser.add_argument('--cmake-generator', default=None, help="CMake generator name")
    parser.add_argument('--generate-project', default=False, action='store_true', help="Generate sample project")
    parser.add_argument('--generate-config', default=False, action='store_true', help="Generate config file")

    parser.add_argument('--conan', help="""
        Conan package manager executable path. Options: [<path to executable>, 'conan', 'local'] Default: 'local'. Option 'conan' will search in path first.
        If conan not present in path it will download conan executable and use it.
    """, nargs='?', const='conan')
    parser.add_argument('--vcpkg', help="""
        VCPKG package manager executable path. Options: [<path to executable>, 'vcpkg', 'local'] Default: 'local'. Option 'vcpkg' will search in path first.
        If vcpkg not present in path it will download conan executable and use it.
    """, nargs='?', const='vcpkg')
    
    args = parser.parse_args()
    args = BuildArgs.parseArgs(args)

    #Create workspace directory
    workspace_directory = f'{args.workdir}/{args.workspace_dir_name}'
    os.makedirs(workspace_directory, exist_ok=True)

    #Download package managers if necessary
    if len(args.conan_path) == 0:
        if conan.is_conan_in_path():
            args.conan_path = commons.realpath(shutil.which("conan"))
        else:
            args.conan_path = conan.download_conan(args.workdir, args.workspace_dir_name)
    
    if len(args.vcpkg_path) == 0:
        if vcpkg.is_vcpkg_in_path():
            args.vcpkg_path = commons.realpath(shutil.which("vcpkg"))
        else:
            args.vcpkg_path = vcpkg.download_vcpkg(workspace_directory)
    
    conan.set_conan_exe(conan_exe=args.conan_path)
    vcpkg.set_exec_file(vcpkg_exe=args.vcpkg_path)
    
    if args.generate_project:
        if platform.system() != "Windows" and args.clion == True:
            print("CLion generation is supported for conan only and windows for now.")
            sys.exit(-1)
        projgen.generate_project(args.conan_path, args.vcpkg_path, args.workdir, args.workspace_dir_name, args.clion)

    if args.dependencies:
        conan.create_profiles(args.workdir, workspace_directory)
        conan.install_dependencies(args.mode, args.workdir, workspace_directory)
        if os.path.exists(f'{args.workdir}/vcpkg.json'):
            vcpkg.install_dependencies(args.workdir, workspace_directory)

    if args.build or args.rebuild or args.config:
        cmake.setup_paths(cmake_exe=args.cmake_path, base_path=args.workdir, workspace_dir_name=args.workspace_dir_name)

        if args.rebuild:
            cmake.delete_cache(args.mode)
        if args.rebuild or args.config:
            cmake.configure(
                args.mode, 
                conan.get_toolchain_filepath(args.mode, workspace_directory), 
                vcpkg.find_dependencies_cmakes(args.workdir, workspace_directory),
                args.generator
            )
        if args.build or args.rebuild:
            cmake.build(config=args.mode)

if __name__ == "__main__":
    main()
    