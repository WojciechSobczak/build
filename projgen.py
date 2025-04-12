import platform
import io
import xml.etree
import xml.etree.ElementTree
import xml.etree.cElementTree
import commons
import os
import jinja2
import xml

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

def generate_clion_workspace(output_directory: str, workdir: str, workspace_dir_name: str):
    CLION_WORKSPACE_FILE = f"{output_directory}/.idea/workspace.xml"

    base_file_path = f"{_BASE_PROJGEN_FILES_PATH}/clion_workspace.xml" 
    if os.path.exists(CLION_WORKSPACE_FILE):
        base_file_path = CLION_WORKSPACE_FILE
    with open(base_file_path, "r", encoding="UTF-8") as f:
        xml_text = f.read()

    def _find_or_create_cmake_component(tree: xml.etree.ElementTree.Element) -> xml.etree.ElementTree.Element:
        components = tree.findall('component')
        cmake_settings = None
        for component in components:
            found_settings = component.attrib['name']
            if found_settings == "CMakeSettings":
                cmake_settings = component
                break
        if cmake_settings == None:
            cmake_settings = xml.etree.ElementTree.SubElement(tree, 'component')
            cmake_settings.attrib['name'] = "CMakeSettings"
        return cmake_settings
    
    def _find_or_create_cmake_configurations(tree: xml.etree.ElementTree.Element) -> xml.etree.ElementTree.Element:
        configurations = tree.find('configurations')
        if configurations == None:
            configurations = xml.etree.ElementTree.SubElement(tree, 'configurations')
        return configurations
    
    def _find_or_create_cmake_profile(tree: xml.etree.ElementTree.Element, name: str, attributes: dict[str, str]):
        configurations = tree.findall('configuration')
        found = False
        for config in configurations:
            if config.attrib["PROFILE_NAME"] == name:
                for key, value in attributes.items():
                    config.attrib[key] = value
                found = True
                break
        if found == False:
            config = xml.etree.ElementTree.SubElement(tree, 'configuration')
            config.attrib["PROFILE_NAME"] = name
            for key, value in attributes.items():
                config.attrib[key] = value

    xml_tree = xml.etree.ElementTree.fromstring(xml_text)
    cmake_settings = _find_or_create_cmake_component(xml_tree)
    configurations = _find_or_create_cmake_configurations(cmake_settings)
    
    workspace_path = f"{workdir}/{workspace_dir_name}"
    import conan
    _find_or_create_cmake_profile(configurations, "VSDebug", {
        "TOOLCHAIN_NAME": "Visual Studio",
        "CONFIG_NAME": "Debug",
        "ENABLED": "true",
        "GENERATION_OPTIONS" : f'-DCMAKE_TOOLCHAIN_FILE="{conan.get_toolchain_filepath("debug")}"',
        "NO_GENERATOR": "true",
        "GENERATION_DIR": f"{workspace_path}/build/vsdebug"
    })
    _find_or_create_cmake_profile(configurations, "VSRelease", {
        "TOOLCHAIN_NAME": "Visual Studio",
        "CONFIG_NAME": "Release",
        "ENABLED": "false",
        "GENERATION_OPTIONS" : f'-DCMAKE_TOOLCHAIN_FILE="{conan.get_toolchain_filepath("release")}"',
        "NO_GENERATOR": "true",
        "GENERATION_DIR": f"{workspace_path}/build/vsrelease"
    })

    os.makedirs(os.path.dirname(CLION_WORKSPACE_FILE), exist_ok=True)
    with open(CLION_WORKSPACE_FILE, "w+", encoding="UTF-8") as f:
        xml.etree.ElementTree.indent(xml_tree)
        f.write(xml.etree.ElementTree.tostring(xml_tree, encoding="UTF-8").decode())
    

def generate_project(package_manager: str, package_manager_path: str, output_directory: str, workspace_dir_name: str, clion: bool):
    output_directory = commons.realpath(output_directory)

    if clion == True:
        generate_clion_workspace(output_directory, output_directory, workspace_dir_name)

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





