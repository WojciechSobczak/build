import platform
import io
import commons
import os
import jinja2

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
    
def generate_nasm_file() -> str:
    with open(f"{_BASE_PROJGEN_FILES_PATH}/assembly.nasm", "r", encoding="utf-8") as file:
        return file.read()

def jinja_exception(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    raise Exception(f"[JINJA ERROR] {output.getvalue()}")


def generate_project(package_manager: str, package_manager_path: str, output_directory: str):
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


    template_loader = jinja2.FileSystemLoader(searchpath=_BASE_PROJGEN_FILES_PATH)
    environment = jinja2.Environment(loader=template_loader)
    environment.globals.update(jinja_exception = jinja_exception)
    templates_variables = {
        'package_manager_name': package_manager,
        'package_manager_path': package_manager_path,
        'project_path': output_directory,
        'script_path': commons.realpath(f"{os.path.dirname(__file__)}/build.py")
    }
    
    with open(f"{output_directory}/build.py", "w", encoding="utf8") as generated_python_file:
        build_py_template = environment.get_template("build.py.jinja2")
        build_py_rendered = build_py_template.render(templates_variables)
        generated_python_file.write(build_py_rendered)

    if platform.system() == "Windows":
        with open(f"{output_directory}/build.bat", "w", encoding="utf8") as generated_bat_file:
            build_bat_template = environment.get_template("build.bat.jinja2")
            build_bat_rendered = build_bat_template.render(templates_variables)
            generated_bat_file.write(build_bat_rendered)
    else:
        with open(f"{output_directory}/build.sh", "w", encoding="utf8") as generated_sh_file:
            build_sh_template = environment.get_template("build.sh.jinja2")
            build_sh_rendered = build_sh_template.render(templates_variables)
            generated_sh_file.write(build_sh_rendered)

    with open(f"{output_directory}/src/assembly.nasm", "w", encoding="utf8") as file:
        file.write(generate_nasm_file())
    
    with open(f"{output_directory}/src/main.cpp", "w", encoding="utf8") as file:
        file.write(generate_main_file())





