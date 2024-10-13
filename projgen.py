import textwrap
import commons
import os

def generate_conanfile() -> str:
    return textwrap.dedent("""
        [requires]
        fmt/11.0.2
        ctre/3.9.0

        [generators]
        CMakeDeps
        CMakeToolchain

        [layout]
        cmake_layout
    """).lstrip()

def generate_vcpkg() -> str:
    return textwrap.dedent("""
        {
            "dependencies": [
                "ctre", 
                "fmt"
            ]
        }
    """).lstrip()

def generate_python_executor(output_directory: str) -> str:
    return textwrap.dedent(f"""
        python3 build.py -w {commons.realpath(output_directory)} -d
    """).lstrip()

def generate_main_file() -> str:
    return textwrap.dedent("""
        #include <fmt/format.h>
        #include <ctre.hpp>

        int main() {
            std::string helloWorld = "Hello World!";
            if (ctre::match<"Hello.*">(helloWorld)) {
                fmt::println("{}", helloWorld);
            }
            return 0;
        }
    """).lstrip()

def generate_cmake_file() -> str:
    return textwrap.dedent("""
        cmake_minimum_required(VERSION 3.21)
        project(generated_project)
        set(CMAKE_CXX_STANDARD 23)

        find_package(ctre REQUIRED)
        find_package(fmt REQUIRED)

        add_executable(${PROJECT_NAME} "src/main.cpp")

        target_link_libraries(${PROJECT_NAME} PUBLIC ctre::ctre)
        target_link_libraries(${PROJECT_NAME} PUBLIC fmt::fmt)
    """).lstrip()


def generate_project(package_manager: str, output_directory: str):
    output_directory = commons.realpath(output_directory)
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(f"{output_directory}/src/", exist_ok=True)

    if package_manager == "conan":
        with open(f"{output_directory}/conanfile.txt", "w", encoding="utf8") as file:
            file.write(generate_conanfile())

    if package_manager == "vcpkg":
        with open(f"{output_directory}/vcpkg.json", "w", encoding="utf8") as file:
            file.write(generate_vcpkg())

    with open(f"{output_directory}/CMakeLists.txt", "w", encoding="utf8") as file:
        file.write(generate_cmake_file())

    with open(f"{output_directory}/src/main.cpp", "w", encoding="utf8") as file:
        file.write(generate_main_file())
