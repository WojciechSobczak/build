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
from package_manager import PackageManager

@dataclasses.dataclass
class BuildArgs:
    build: bool
    rebuild: bool
    config: bool
    workdir: str
    mode: str
    conan_path: str | None
    vcpkg_path: str | None
    package_manager: PackageManager
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
    def parse_args_and_setup_tools(args: argparse.Namespace) -> 'BuildArgs':
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
        if cmake_path is None:
            raise Exception("Argparse error: if cmake is not available in PATH, 'cmake-path' must be set to path to executable")

        conan_path: str | None = None
        vcpkg_path: str | None = None
        package_manager: PackageManager = PackageManager.ALL

        workspace_directory = f'{args.workdir}/{args.workspace_dir_name}'
        if args.package_manager == "conan" or args.package_manager == "all":
            conan_path = BuildArgs._extract_path(args.conan)
            if conan_path is None:
                conan_path = conan.download_conan(workspace_directory)
            package_manager = PackageManager.CONAN
        elif args.package_manager == "vcpkg" or args.package_manager == "all":
            vcpkg_path = BuildArgs._extract_path(args.vcpkg)
            if vcpkg_path is None:
                vcpkg_path = vcpkg.download_vcpkg(workspace_directory)
            package_manager = PackageManager.VCPKG
        elif args.package_manager == "all":
            package_manager = PackageManager.ALL
        else:
            raise Exception("Argparse error: Package manager must be set.")
        
        return BuildArgs(
            build = args.build, 
            rebuild = args.rebuild,
            config = args.cmake_config,
            workdir = commons.realpath(args.workdir),
            mode = mode,
            dependencies = args.dependencies,
            conan_path = conan_path,
            cmake_path = cmake_path,
            vcpkg_path = vcpkg_path,
            package_manager = package_manager,
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
    parser.add_argument('--generate-project', '--projgen', default=False, action='store_true', help="Generate sample project")
    parser.add_argument('--generate-config', '--confgen', default=False, action='store_true', help="Generate config file")
    parser.add_argument('--package-manager', default="conan", help="Package manager to generate project with.", choices=["conan", "vcpkg", "all"])
    parser.add_argument('--conan', help="""
        Conan package manager executable path. Options: [<path to executable>, 'conan'] 
        Default: 'conan'. Option 'conan' will search in path first.
        If conan not present in path it will download conan executable and use it.
    """, nargs='?', const='conan')
    parser.add_argument('--vcpkg', help="""
        VCPKG package manager executable path. Options: [<path to executable>, 'vcpkg'] 
        Default: 'vcpkg'. Option 'vcpkg' will search in path first.
        If vcpkg not present in path it will download conan executable and use it.
    """, nargs='?', const='vcpkg')
    
    args = parser.parse_args()
    args = BuildArgs.parse_args_and_setup_tools(args)

    #Create workspace directory
    workspace_directory = f'{args.workdir}/{args.workspace_dir_name}'
    os.makedirs(workspace_directory, exist_ok=True)
    
    if args.generate_project:
        if platform.system() != "Windows" and args.clion == True:
            raise Exception("CLion generation is supported for conan only and windows for now.")
        projgen.generate_project(
            package_manager=args.package_manager, 
            conan_exe=args.conan_path, 
            vcpkg_exe=args.vcpkg_path, 
            output_directory=args.workdir,
            workspace_dir_name=args.workspace_dir_name,
            clion=args.clion
        )

    if args.dependencies:
        if args.package_manager == PackageManager.CONAN or args.package_manager == PackageManager.ALL:
            if not os.path.exists(f'{args.workdir}/conanfile.txt'):
                raise Exception("Conan chosen as package manager, but conanfile.txt does not exist.")
            conan.create_profiles(args.conan_path, args.workdir, workspace_directory)
            conan.install_dependencies(args.conan_path, args.mode, args.workdir, workspace_directory)
        if args.package_manager == PackageManager.VCPKG or args.package_manager == PackageManager.ALL:
            if not os.path.exists(f'{args.workdir}/vcpkg.json'):
                raise Exception("Vcpkg chosen as package manager, but vcpkg.json does not exist.")
            vcpkg.install_dependencies(args.vcpkg_path, args.workdir, workspace_directory)

    if args.build or args.rebuild or args.config:
        cmake.setup_paths(cmake_exe=args.cmake_path, base_path=args.workdir, workspace_dir_name=args.workspace_dir_name)
        if args.rebuild:
            cmake.delete_cache(args.mode)
        if args.rebuild or args.config:
            cmake.configure(
                config=args.mode, 
                package_manager=args.package_manager, 
                project_dir=args.workdir, 
                workspace_dir=workspace_directory,
                vcpkg_exe=args.vcpkg_path,
                generator=args.generator
            )
        if args.build or args.rebuild:
            cmake.build_project(config=args.mode)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(-1)
    