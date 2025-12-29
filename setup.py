import os
import shutil
import urllib.request
import zipfile
import argparse

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
MASTER_LINK = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"
RELEASE_LINK = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"
GITHUB_ZIP_PREFIX = "build-master/"
DEFAULT_WORKSPACE_NAME = ".workspace"

def setup_build_tools(workspace_folder: str, workspace_name: str, working_dir: str, generate_project: bool):
    zip_path = f"{workspace_folder}/build_tools.zip"
    extract_path = f"{workspace_folder}/build_tools"
    projgen_files = f"{extract_path}/projgen_files"
    
    os.makedirs(workspace_folder, exist_ok=True)
    os.makedirs(extract_path, exist_ok=True)

    urllib.request.urlretrieve(RELEASE_LINK, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_infos = zip_file.infolist()
        for zip_info in zip_infos:
            if zip_info.filename == GITHUB_ZIP_PREFIX:
                continue
            zip_info.filename = zip_info.filename.replace(GITHUB_ZIP_PREFIX, '')
            zip_file.extract(zip_info, extract_path)

    os.remove(zip_path)
    
    source_build_py = f'{extract_path}/build_user_file.py'
    dest_build_py = f'{working_dir}/build.py'
    git_ignore = f'{working_dir}/.gitignore'

    with open(source_build_py, "r", encoding="UTF-8") as input:
        text = input.read()
        text = text.replace(MASTER_LINK, RELEASE_LINK)
        if workspace_name != DEFAULT_WORKSPACE_NAME:
            text = text.replace(
                DEFAULT_WORKSPACE_NAME,
                workspace_name
            )
    with open(dest_build_py, "w", encoding="UTF-8") as output:
        output.write(text)

    if generate_project:
        files_to_copy: dict[str, str] = {
            f'{projgen_files}/CMakeLists.txt' : f'{working_dir}/CMakeLists.txt',
            f'{projgen_files}/conanfile.txt' : f'{working_dir}/conanfile.txt',
            f'{projgen_files}/vcpkg.json' : f'{working_dir}/vcpkg.json',
            f'{projgen_files}/main.cpp' : f'{working_dir}/src/main.cpp',
            f'{projgen_files}/assembly.nasm' : f'{working_dir}/src/assembly.nasm'
        }

        for _from, to in files_to_copy.items():
            os.makedirs(os.path.dirname(to), exist_ok=True)
            shutil.copyfile(_from, to)

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

def main():
    parser = argparse.ArgumentParser(description="Wojciech's C++ project setup")
    parser.add_argument('-g', '--generate-project', default=False, action='store_true', help="Generate basic project.")
    parser.add_argument('-w', '--workspace-name', default=DEFAULT_WORKSPACE_NAME, help="Created workspace name")
    args = parser.parse_args()
    
    workspace_folder = f"{SCRIPT_DIR}/{args.workspace_name}"
    print(f"[SETUP.PY] CWD: {SCRIPT_DIR} | WORKSPACE: {workspace_folder}")
    setup_build_tools(workspace_folder, args.workspace_name, SCRIPT_DIR, args.generate_project)

if __name__ == "__main__":
    main()