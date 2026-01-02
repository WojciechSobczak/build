import os
import shutil
import urllib.request
import zipfile
import argparse

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')

RELEASE_ZIP_LINK = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"

MASTER_SETUP_PY_LINK = "https://github.com/WojciechSobczak/build/blob/master/setup.py"
RELEASE_SETUP_PY_LINK = "https://github.com/WojciechSobczak/build/blob/master/setup.py"

GITHUB_ZIP_PREFIX = "build-master/"
DEFAULT_WORKSPACE_NAME = ".workspace"

def log(msg: str):
    print(f"[BUILD_TOOLS][SETUP.PY] {msg}", flush=True)

def setup_build_tools(workspace_folder: str, workspace_name: str, working_dir: str, generate_project: bool, overwrite_files: bool):
    zip_path = f"{workspace_folder}/build_tools.zip"
    extract_path = f"{workspace_folder}/build_tools"
    projgen_files_dir = f"{extract_path}/build_tools/projgen_files"
    template_build_py_path = f'{extract_path}/build_user_file.py'
    created_build_py_path = f'{working_dir}/build.py'

    def _add_prefix_and_yell_if_exists(file_path: str):
        if os.path.exists(file_path) and not overwrite_files:
            log(f"Default project file '{file_path}' already exists. Adding '.bt_exists' suffix to avoid overrides")
            file_path += ".bt_exists"
        return file_path

    #START: Downloading the build_tools files
    log('Downloading the build_tools files...')
    os.makedirs(workspace_folder, exist_ok=True)
    os.makedirs(extract_path, exist_ok=True)
    urllib.request.urlretrieve(RELEASE_ZIP_LINK, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_infos = zip_file.infolist()
        for zip_info in zip_infos:
            if zip_info.filename == GITHUB_ZIP_PREFIX:
                continue
            zip_info.filename = zip_info.filename.replace(GITHUB_ZIP_PREFIX, '')
            zip_file.extract(zip_info, extract_path)
    os.remove(zip_path)
    #END: Downloading the build_tools files

    #START: Generating build.py for the project
    log('Generating build.py for the project...')
    with open(template_build_py_path, "r", encoding="UTF-8") as input:
        text = input.read()
        text = text.replace(MASTER_SETUP_PY_LINK, RELEASE_SETUP_PY_LINK)
        if workspace_name != DEFAULT_WORKSPACE_NAME:
            text = text.replace(
                DEFAULT_WORKSPACE_NAME,
                workspace_name
            )

    created_build_py_path = _add_prefix_and_yell_if_exists(created_build_py_path)
    with open(created_build_py_path, "w", encoding="UTF-8") as output:
        output.write(text)
    #END: Generating build.py for the project

    if generate_project:
        #START: Copying the default project files
        log('Copying the default project files...')
        files_to_copy: dict[str, str] = {
            f'{projgen_files_dir}/CMakeLists.txt' : f'{working_dir}/CMakeLists.txt',
            f'{projgen_files_dir}/conanfile.txt' : f'{working_dir}/conanfile.txt',
            f'{projgen_files_dir}/vcpkg.json' : f'{working_dir}/vcpkg.json',
            f'{projgen_files_dir}/main.cpp' : f'{working_dir}/src/main.cpp',
            f'{projgen_files_dir}/assembly.nasm' : f'{working_dir}/src/assembly.nasm'
        }

        for _from, to in files_to_copy.items():
            os.makedirs(os.path.dirname(to), exist_ok=True)
            to = _add_prefix_and_yell_if_exists(to)
            shutil.copyfile(_from, to)

        git_ignore = _add_prefix_and_yell_if_exists(f'{working_dir}/.gitignore')
        with open(git_ignore, "w", encoding="UTF-8") as output:
            for ignore_file in [
                f"{workspace_name}",
                f"__pycache__",
                f".vscode",
                f".idea",
                f".vs",
                f".mypy_cache",
                f"CMakeUserPresets.json"
            ]:
                output.write(f'{ignore_file}\n')
            output.write('\n')
        #END: Copying the default project files

        #START: Creating .env file
        log('Creating .env file...')
        env_file_path = _add_prefix_and_yell_if_exists(f"{working_dir}/.env")
        with open(env_file_path, "w", encoding="UTF-8") as file:
            file.write(f'PYTHONPATH="$PYTHONPATH;{workspace_folder}/build_tools"')
        #END: Creating .env file 
    

def main():
    parser = argparse.ArgumentParser(description="Wojciech's C++ project setup")
    parser.add_argument('-g', '--generate-project', default=False, action='store_true', help="Generate basic project.")
    parser.add_argument('-w', '--workspace-name', default=DEFAULT_WORKSPACE_NAME, help="Created workspace name")
    parser.add_argument('-o', '--overwrite-files', default=False, action='store_true', help="Don't protect files from being overwrite")
    args = parser.parse_args()
    
    workspace_folder = f"{SCRIPT_DIR}/{args.workspace_name}"
    print(f"[BUILD_TOOLS][SETUP.PY] CWD: {SCRIPT_DIR} | WORKSPACE: {workspace_folder}")
    setup_build_tools(workspace_folder, args.workspace_name, SCRIPT_DIR, args.generate_project, args.overwrite_files)
    print(f"[BUILD_TOOLS][SETUP.PY] Finished successfully.")

if __name__ == "__main__":
    main()