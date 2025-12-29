import os
import shutil
import urllib.request
import zipfile
import argparse

def setup_build_tools(workspace_folder: str, workspace_name: str, working_dir: str, generate_project: bool):
    link = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"
    zip_path = f"{workspace_folder}/build_tools.zip"
    extract_path = f"{workspace_folder}/build_tools"
    projgen_files = f"{extract_path}/projgen_files"
    github_prefix = 'build-master/'
    
    os.makedirs(workspace_folder, exist_ok=True)
    os.makedirs(extract_path, exist_ok=True)

    urllib.request.urlretrieve(link, zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_infos = zip_file.infolist()
        for zip_info in zip_infos:
            if zip_info.filename == github_prefix:
                continue
            zip_info.filename = zip_info.filename.replace(github_prefix, '')
            zip_file.extract(zip_info, extract_path)

    os.remove(zip_path)
    
    source_build_py = f'{extract_path}/build_user_file.py'
    dest_build_py = f'{working_dir}/build.py'

    if workspace_name == f".workspace":
        shutil.copyfile(source_build_py, dest_build_py)
    else:
        with open(source_build_py, "r", encoding="UTF-8") as input:
            text = input.read()
        with open(dest_build_py, "w", encoding="UTF-8") as output:
            text = text.replace(
                f".workspace",
                workspace_name
            )
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

def main():
    parser = argparse.ArgumentParser(description="Wojciechs C++ project setup")
    parser.add_argument('-g', '--generate-project', default=False, action='store_true', help="Generate basic project.")
    parser.add_argument('-w', '--workspace-name', default=".workspace", help="Crated workspace path")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
    workspace_folder = f"{script_dir}/{args.workspace_name}"
    print(f"[SETUP.PY] CWD: {script_dir} | WORKSPACE: {workspace_folder}")
    setup_build_tools(workspace_folder, args.workspace_name, script_dir, args.generate_project)

if __name__ == "__main__":
    main()