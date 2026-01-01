import os
import textwrap
import typing
import xml.etree.ElementTree

from . import conan
from . import log
from . import commons
from . import config
from . import cmake

def _error_log_and_die(msg: str) -> typing.NoReturn:
    log.error(msg)
    exit(-1)


def create_build_tools_configurations(
    cmake_config: cmake.Config,
    toolset_config: config.BuildToolsConfig,
    vcpkg_dependencies: list[str] | None = None
):
    log.info("Creating CLion Project XML File with CMake settings...")
    _create_idea_project_xml(cmake_config, toolset_config, vcpkg_dependencies)
    log.info("Creating CLion basic dictionary...")
    _create_idea_dictionary_xml(toolset_config.project_dir)
    log.info("Creating CLion files finished successfully!")

def _create_idea_project_xml(
    cmake_config: cmake.Config,
    toolset_config: config.BuildToolsConfig,
    vcpkg_dependencies: list[str] | None = None
):
    IDEA_WORKSPACE_FILE = f'{toolset_config.project_dir}/.idea/workspace.xml'
    os.makedirs(os.path.dirname(IDEA_WORKSPACE_FILE), exist_ok=True)
    if not os.path.exists(IDEA_WORKSPACE_FILE):
        with open(IDEA_WORKSPACE_FILE, "w", encoding="UTF-8") as file:
            file.write(textwrap.dedent("""
                <project version="4">
                    <component name="CMakeSettings">
                        <configurations>
                        </configurations>
                    </component>
                </project>
            """).strip())

    tree = xml.etree.ElementTree.parse(IDEA_WORKSPACE_FILE)
    project = tree.getroot()
    if project.tag != "project":
        _error_log_and_die('<project> tag not found in .idea/workspace.xml. Process of creating config aborted.')
    if project.attrib['version'] != "4":
        _error_log_and_die("<project> version is different from 4, which is not supported")


    cmake_settings = project.find('./component[@name="CMakeSettings"]')
    if cmake_settings is None:
        cmake_settings = xml.etree.ElementTree.SubElement(project, 'component', {"name" : "CMakeSettings"})

    # Read all configurations
    configurations_element = cmake_settings.find('./configurations')
    if configurations_element is None:
        configurations_element = xml.etree.ElementTree.SubElement(cmake_settings, 'configurations')
    # Save list of all of them
    configuration_list = configurations_element.findall('./configuration')
    # Clear all configurations 
    configurations_element.clear()

    # Disable all and filter build_tools created ones
    for config in configuration_list:
        config.attrib["ENABLED"] = "False"
    configuration_list = [config for config in configuration_list if config.attrib['PROFILE_NAME'] not in ["Debug", "Release"]]

    # Reinsert all filtered configs back
    for index, config in enumerate(configuration_list):
        configurations_element.insert(index, config)

    # Create all build_tools configs
    for mode in ["Debug", "Release"]:
        toolchain_file = conan.get_toolchain_filepath(
            mode.capitalize(), 
            toolset_config.workspace_dir, 
            toolset_config.is_ninja_set()
        )
        toolchain_file = commons.normalize_path(toolchain_file)
        cmake_options = cmake.generate_configure_options(cmake_config, toolset_config, vcpkg_dependencies)
        generation_options: list[str] = []
        for key, value in cmake_options.variables.items():
            generation_options += [f'{key}="{value}"']

        toolchain_name = "Visual Studio" if commons.is_windows() else "Unix Makefiles"
        build_options = ["-j16"] if toolset_config.is_ninja_set() else []

        new_config: dict[str, str] = {
            "PROFILE_NAME" : mode,
            "ENABLED" : "true",
            "GENERATION_DIR" : f"$PROJECT_DIR$/.workspace/clion/{mode.lower()}",
            "GENERATION_OPTIONS": ' '.join(generation_options),
            "CONFIG_NAME" : mode,
            "TOOLCHAIN_NAME": toolchain_name,
            "BUILD_OPTIONS" : ' '.join(build_options),
            "NO_GENERATOR" : "true"
        }

        xml.etree.ElementTree.SubElement(configurations_element, 'configuration', new_config)

    tree.write(IDEA_WORKSPACE_FILE)
    
    log.warn("----------------- [CLION IMPORTANT NOTE] ---------------------")
    log.warn("There is no way to enforce CMake version inside CLion single project")
    log.warn("If you want to use build_tools downloaded CMake version you have to")
    log.warn("create custom global CLion Toolchain and set the executable yourself")
    log.warn("For CLion version 2025.03 there is no way around it. Sorry.")
    log.warn("You have to setup: Preferences > Build, Execution, Deployment > Toolchains > YOUR_TOOLCHAIN > CMake")
    log.warn("----------------- [CLION IMPORTANT NOTE] ---------------------")

def _create_idea_dictionary_xml(project_dir: str):
    IDEA_DICTIONARY_FILE = f'{project_dir}/.idea/dictionaries/project.xml'
    os.makedirs(os.path.dirname(IDEA_DICTIONARY_FILE), exist_ok=True)
    if not os.path.exists(IDEA_DICTIONARY_FILE):
        with open(IDEA_DICTIONARY_FILE, "w", encoding="UTF-8") as file:
            file.write(textwrap.dedent("""
                <component name="ProjectDictionaryState">
                    <dictionary name="project">
                        <words>
                        </words>
                    </dictionary>
                </component>
            """).strip())


    tree = xml.etree.ElementTree.parse(IDEA_DICTIONARY_FILE)
    project_dictionary_state = tree.getroot()
    if project_dictionary_state.tag != "component" and project_dictionary_state.attrib['name'] != "ProjectDictionaryState":
        log.warn('<component name="ProjectDictionaryState"> Not found in dictionary file. Omitting dictionary generation')
        return
    
    project_dictionary = project_dictionary_state.find('./dictionary[@name="project"]')
    if project_dictionary is None:
        project_dictionary = xml.etree.ElementTree.SubElement(project_dictionary_state, 'dictionary', attrib={'name' : "project"})
    
    project_dictionary_words = project_dictionary.find('./words')
    if project_dictionary_words is None:
        project_dictionary_words = xml.etree.ElementTree.SubElement(project_dictionary, 'words')

    for word_text in ["ctre"]:
        word = xml.etree.ElementTree.SubElement(project_dictionary_words, 'word')
        word.text = word_text

    tree.write(IDEA_DICTIONARY_FILE)
