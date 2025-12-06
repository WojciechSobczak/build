import os
import subprocess
import urllib.request
import zipfile
import shutil

def setup_build_tools(workspace_folder: str, working_dir: str):
    link = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"
    zip_path = f"{workspace_folder}/build_tools.zip"
    extract_path = f"{workspace_folder}/build_tools"
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

    build_file_path = f'{extract_path}/build_user_file.py'
    build_dest_path = f'{working_dir}/build.py'
    shutil.copyfile(build_file_path, build_dest_path)

    pip_install_command = f"pip install -r {extract_path}/requirements.txt"
    process = subprocess.run(
        args=f"pip install -r {extract_path}/requirements.txt", 
        cwd = working_dir, 
        shell=True
    )
    if process.returncode != 0:
        print(f"[SETUP.PY ERROR] {pip_install_command} failed! Error code: {process.returncode}")
        exit(-1)

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    workspace_folder = f"{script_dir}/.workspace"
    setup_build_tools(workspace_folder, script_dir)

if __name__ == "__main__":
    main()