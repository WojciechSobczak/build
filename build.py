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
    workdir: str
    mode: str
    package_manager_path: str
    dependencies: bool
    cmake_path: str
    package_manager: str
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
        
        if args.vcpkg == "" and args.conan == "":
            args.conan = "conan"
            print("[WARNING] No package manager has been set. Conan used by default.")

        if args.conan != "":
            package_manager = "conan"
            package_manager_path = BuildArgs._extract_path(args.conan)
            package_manager_path = BuildArgs._get_absolute_path(args.conan)
        else:
            package_manager = "vcpkg"
            package_manager_path = BuildArgs._extract_path(args.vcpkg)
            package_manager_path = BuildArgs._get_absolute_path(args.vcpkg)
        
        return BuildArgs(
            build = args.build, 
            rebuild = args.rebuild,
            workdir = commons.realpath(args.workdir),
            mode = mode,
            package_manager_path = package_manager_path, # type: ignore
            dependencies = args.dependencies,
            cmake_path = cmake_path, # type: ignore
            package_manager = package_manager,
            generator = args.cmake_generator,
            generate_project = args.generate_project,
            generate_config = args.generate_config,
            clion = args.clion,
            workspace_dir_name = args.workspace_dir_name
        )

def setup_package_manager_paths(args: BuildArgs):
    if args.package_manager == "conan":
        conan.setup_paths(conan_exe=args.package_manager_path, base_path=args.workdir, workspace_dir_name = args.workspace_dir_name)
    if args.package_manager == "vcpkg":
        vcpkg.setup_paths(vcpkg_exe=args.package_manager_path, base_path=args.workdir, workspace_dir_name = args.workspace_dir_name)

def main():
    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-w', '--workdir', help="Script working directory.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="debug", help="CMake build mode. Either 'debug' or 'release' (case insensitive).")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    parser.add_argument('--workspace-dir-name', help="Workspace files directory name", default=".workspace")
    parser.add_argument('--conan', help="Enable conan2 as package manager. Optional: conan2 executable path", nargs='?', const='conan')
    parser.add_argument('--clion', help="Generate files for CLion IDE", default=False, action='store_true')
    parser.add_argument('--vcpkg', help="Enable vcpkg as package manager. Optional: vcpkg executable path", nargs='?', const='vcpkg')
    parser.add_argument('--cmake-path', default="cmake", help="cmake executable path")
    parser.add_argument('--cmake-generator', default=None, help="CMake generator name")
    parser.add_argument('--generate-project', default=False, action='store_true', help="Generate sample project")
    parser.add_argument('--generate-config', default=False, action='store_true', help="Generate config file")
    
    args = parser.parse_args()
    args = BuildArgs.parseArgs(args)

    #Create workspace directory
    os.makedirs(f'{args.workdir}/{args.workspace_dir_name}', exist_ok=True)

    #Download conan if necessary
    if args.package_manager == "conan":
        if conan.is_conan_in_path() == False:
            args.package_manager_path = conan.download_conan(args.workdir, args.workspace_dir_name)

    if args.generate_project:
        if args.package_manager != "conan" or platform.system() != "Windows":
            print("CLion generation is supported for conan only and windows for now.")
            sys.exit(-1)

        setup_package_manager_paths(args)
        projgen.generate_project(args.package_manager, args.package_manager_path, args.workdir, args.workspace_dir_name, args.clion)

    if args.dependencies:
        setup_package_manager_paths(args)
        if args.package_manager == "conan":
            conan.create_profiles()
            conan.install_dependencies(args.mode)
        if args.package_manager == "vcpkg":
            vcpkg.install_dependencies()
    
    if args.build or args.rebuild:
        cmake.setup_paths(cmake_exe=args.cmake_path, base_path=args.workdir, workspace_dir_name=args.workspace_dir_name)

        if args.package_manager == "conan":
            conan.setup_paths(conan_exe=args.package_manager_path, base_path=args.workdir, workspace_dir_name=args.workspace_dir_name)
            package_manager = cmake.ConanPackageManager(conan.get_toolchain_filepath(args.mode))
        else:
            package_manager = cmake.VcpkgPackageManager(args.package_manager_path)
        
        if args.rebuild:
            cmake.delete_cache(args.mode)
            cmake.configure(args.mode, package_manager, args.generator)
        if args.build:
            cmake.build(config=args.mode)

if __name__ == "__main__":
    main()
    