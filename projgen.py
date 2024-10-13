import enum
import commons
import os

_BASE_PROJGEN_FILES_PATH = f"{os.path.dirname(os.path.realpath(__file__))}/projgen_files/"

def generate_conanfile() -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/conanfile.txt", "r", encoding="utf-8") as file:
        return file.read()

def generate_vcpkg() -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/vcpkg.json", "r", encoding="utf-8") as file:
        return file.read()
    
def generate_main_file() -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/main.cpp", "r", encoding="utf-8") as file:
        return file.read()
    
def generate_cmake_file() -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/CMakeLists.txt", "r", encoding="utf-8") as file:
        return file.read()

def replace_launcher_variables(text: str, script_name: str, project_path: str):
    text = text.replace("${script_name}", script_name)
    text = text.replace("${project_path}", project_path)
    return text

def generate_python_executor(script_name: str, project_path: str) -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/build.py", "r", encoding="utf-8") as file:
        text = file.read()
    return replace_launcher_variables(text, script_name, project_path)

def generate_batch_executor(script_name: str, project_path: str) -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/build.bat", "r", encoding="utf-8") as file:
        text = file.read()
    return replace_launcher_variables(text, script_name, project_path)

def generate_shell_executor(script_name: str, project_path: str) -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/build.sh", "r", encoding="utf-8") as file:
        text = file.read()
    return replace_launcher_variables(text, script_name, project_path)

class Launcher(enum.Enum):
    PYTHON = enum.auto(),
    BATCH = enum.auto(),
    SHELL = enum.auto()

def generate_script_launcher(launcher: Launcher, project_path: str) -> str:
    script_name = commons.realpath(f"{os.path.dirname(__file__)}/build.py")
    project_path = commons.realpath(project_path)

    match launcher:
        case Launcher.PYTHON: return generate_python_executor(script_name, project_path)
        case Launcher.BATCH: return generate_batch_executor(script_name, project_path) 
        case Launcher.SHELL: return generate_shell_executor(script_name, project_path)

    raise Exception(f"PROJGEN: Non handled generator: {launcher}")


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

    with open(f"{output_directory}/build.py", "w", encoding="utf8") as file:
        file.write(generate_script_launcher(Launcher.PYTHON, output_directory))

    with open(f"{output_directory}/build.sh", "w", encoding="utf8") as file:
        file.write(generate_script_launcher(Launcher.SHELL, output_directory))
    
    with open(f"{output_directory}/build.bat", "w", encoding="utf8") as file:
        file.write(generate_script_launcher(Launcher.BATCH, output_directory))

    with open(f"{output_directory}/src/main.cpp", "w", encoding="utf8") as file:
        file.write(generate_main_file())



