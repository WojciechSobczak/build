import os
import textwrap
import typing
import xml.etree.ElementTree

from . import conan
from . import log
from . import commons

def _log_error_and_throw(mgs: str) -> typing.NoReturn:
    log.error(mgs)
    raise Exception(mgs)

# <component name="CMakeSettings">
#     <configurations>
#       <configuration PROFILE_NAME="bt.Debug" ENABLED="true" GENERATION_DIR=".workspace/clion/debug" CONFIG_NAME="Debug" TOOLCHAIN_NAME="Visual Studio" GENERATION_OPTIONS="-DCMAKE_PREFIX_PATH=&quot;I SEE THAT&quot;" BUILD_OPTIONS="-j16" NO_GENERATOR="true" />
#       <configuration PROFILE_NAME="bt.Release" ENABLED="true" GENERATION_DIR=".workspace/clion/release" CONFIG_NAME="Release" TOOLCHAIN_NAME="Visual Studio" GENERATION_OPTIONS="-DCMAKE_PREFIX_PATH=&quot;I SEE THAT&quot;" BUILD_OPTIONS="-j16" NO_GENERATOR="true" />
#       <configuration PROFILE_NAME="conan-default" ENABLED="false" FROM_PRESET="true" GENERATION_DIR="$PROJECT_DIR$/.workspace/conan2_home/dependencies/debug/build" />
#       <configuration PROFILE_NAME="conan-default - conan-debug" ENABLED="false" FROM_PRESET="true" GENERATION_DIR="$PROJECT_DIR$/.workspace/conan2_home/dependencies/debug/build" />
#     </configurations>
#   </component>

def create_build_tools_configurations(
    workspace_dir: str,
    project_dir: str,
    ninja_exe: str | None = None,
    vcpkg_dependencies: list[str] | None = None
):
    IDEA_WORKSPACE_FILE = f'{project_dir}/.idea/workspace.xml'
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
    project = tree.find('.')
    if project == None:
        _log_error_and_throw('<project> tag not found in .idea/workspace.xml. Process of creating config aborted.')
    if project.attrib['version'] != "4":
        _log_error_and_throw("<project> version is different from 4, which is not supported")


    cmake_settings = project.find('./component[@name="CMakeSettings"]')
    if cmake_settings == None:
        cmake_settings = xml.etree.ElementTree.SubElement(project, 'component', {"name" : "CMakeSettings"})

    # Read all configurations
    configurations_element = cmake_settings.find('./configurations')
    if configurations_element == None:
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
        toolchain_file = conan.get_toolchain_filepath(mode.capitalize(), workspace_dir, ninja_exe != None)
        toolchain_file = commons.normalize_path(toolchain_file)
        generation_options: list[str] = [
            f'-DCMAKE_TOOLCHAIN_FILE="{toolchain_file}"'
        ]
        if vcpkg_dependencies != None:
            generation_options += [
                f'-DCMAKE_PREFIX_PATH="{';'.join(vcpkg_dependencies)}"'
            ]

        toolchain_name = "Visual Studio" if commons.is_windows() else "Unix Makefiles"
        build_options = []
        if ninja_exe != None:
            generation_options += [
                f'-DCMAKE_GENERATOR=Ninja',
                f'-DCMAKE_MAKE_PROGRAM="{ninja_exe}"'
            ]
            build_options += [
                "-j16"
            ]

        #set_target_properties(${_LIB_NAME} PROPERTIES IMPORTED_LOCATION ${CONAN_FOUND_LIBRARY} IMPORTED_NO_SONAME ${no_soname_mode})

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


    IDEA_DICTIONARY_FILE = f'{project_dir}/.idea/dictionaries/project.xml'
    os.makedirs(os.path.dirname(IDEA_DICTIONARY_FILE), exist_ok=True)
    with open(IDEA_DICTIONARY_FILE, "w", encoding="UTF-8") as file:
        file.write(textwrap.dedent("""
            <component name="ProjectDictionaryState">
                <dictionary name="project">
                    <words>
                        <w>ctre</w>
                    </words>
                </dictionary>
            </component>
        """))

    

    