import dataclasses
import os
import argparse
import shutil
import commons
import conan
import cmake
import vcpkg
import projgen



@dataclasses.dataclass
class BuildArgs:
    build: bool
    rebuild: bool
    workdir: str
    mode: str
    conan_path: str
    vcpkg_path: str
    dependencies: bool
    cmake_path: str
    package_manager: str
    generator: str | None
    generate_project: bool

    @staticmethod
    def _extract_path(path: str):
        if ("/" in path or "\\" in path) and os.path.exists(path):
            if not os.path.isfile(path):
                path = None
        if path != None:
            if shutil.which(path) is None:
                path = None
        return path
    
    @staticmethod
    def _get_absolute_path(path: str):
        if "/" in path or "\\" in path:
            return commons.realpath(path)
        path = shutil.which(path)
        if path is not None:
            return commons.normalize_path(path)
        return path

    @staticmethod
    def parseArgs(args: argparse.Namespace) -> 'BuildArgs':
        if args.workdir == None:
            raise Exception("Argparse error: 'workdir' must be set")

        mode: str = args.mode
        mode = mode.lower().strip()
        if mode != "debug" and mode != "release":
            raise Exception("Argparse error: Only 'debug' or 'release' are allowed for mode")

        vcpkg_path: str = BuildArgs._extract_path(args.vcpkg_path)
        conan_path: str = BuildArgs._extract_path(args.conan_path)
        if vcpkg_path is None and conan_path is None:
            raise Exception(
                "Argparse error: 'conan-path' or 'vcpkg-path' must be set and be a path or exe name. " +
                "If declared package manager set without this arguments set, executable must be present in PATH"
            )

        cmake_path: str = BuildArgs._extract_path(args.cmake_path)
        if cmake_path == None:
            raise Exception("Argparse error: 'cmake-path' must be path or exe name")
        
        vcpkg_path = BuildArgs._get_absolute_path(args.vcpkg_path)
        conan_path = BuildArgs._get_absolute_path(args.conan_path)
        cmake_path = BuildArgs._get_absolute_path(args.cmake_path)

        package_manager: str = args.package_manager
        package_manager = package_manager.lower().strip()
        if package_manager != "conan" and package_manager != "vcpkg":
            raise Exception("Argparse error: Only 'conan' or 'vcpkg' are allowed for package-manager")

        return BuildArgs(
            args.build, 
            args.rebuild,
            commons.BASE_PATH if args.workdir is None else args.workdir,
            mode,
            conan_path,
            vcpkg_path,
            args.dependencies,
            cmake_path,
            package_manager,
            args.cmake_generator,
            args.generate_project
        )
        

def main():
    parser = argparse.ArgumentParser(description="Wojciechs build utilities")
    parser.add_argument('-w', '--workdir', help="Script working directory.")
    parser.add_argument('-b', '--build', default=False, action='store_true', help="CMake build.")
    parser.add_argument('-r', '--rebuild', default=False, action='store_true', help="CMake delete cache and rebuild.")
    parser.add_argument('-m', '--mode', default="Release", help="CMake build mode. Either 'Debug' or 'Release'. ")
    parser.add_argument('-d', '--dependencies', default=False, action='store_true', help="Download dependencies")
    parser.add_argument('--package-manager', default="conan", help="Package manager to be used")
    parser.add_argument('--conan-path', default="conan", help="conan2 executable path")
    parser.add_argument('--vcpkg-path', default="vcpkg", help="vcpkg executable path")
    parser.add_argument('--cmake-path', default="cmake", help="cmake executable path")
    parser.add_argument('--cmake-generator', default=None, help="CMake generator name")
    parser.add_argument('--generate-project', default=False, action='store_true', help="Generate sample project")
    
    args = parser.parse_args()
    args = BuildArgs.parseArgs(args)
    commons.BASE_PATH = commons.realpath(args.workdir)

    if args.generate_project:
        projgen.generate_project(args.package_manager, args.workdir)

    if args.dependencies:
        if args.package_manager == "conan":
            conan.setup_paths(
                conan_exe=args.conan_path, 
                base_path=commons.BASE_PATH
            )
            conan.create_profiles()
            conan.install_dependencies(args.mode)
        if args.package_manager == "vcpkg":
            vcpkg.setup_paths(
                vcpkg_exe=args.vcpkg_path, 
                base_path=commons.BASE_PATH
            )
            vcpkg.install_dependencies()
    
    if args.build or args.rebuild:
        cmake.setup_paths(
            cmake_exe=args.cmake_path,
            base_path=commons.BASE_PATH
        )

        if args.package_manager == "vcpkg":
            package_manager = cmake.VcpkgPackageManager(args.vcpkg_path)
        else:
            if args.package_manager != "conan":
                print("[WARNING]: No package manager chosen. Conan set by default.")
            conan.setup_paths(
                conan_exe=args.conan_path, 
                base_path=commons.BASE_PATH
            )
            package_manager = cmake.ConanPackageManager(conan.get_toolchain_filepath(args.mode))

        if args.build:
            cmake.configure(args.mode, package_manager, args.generator)
        if args.rebuild:
            cmake.delete_cache()
            cmake.configure(args.mode, package_manager, args.generator)
            cmake.build(config=args.mode)


if __name__ == "__main__":
    main()