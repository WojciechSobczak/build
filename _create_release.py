import os
import sys
import argparse
import re

from build_tools import commons

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
sys.path.append(SCRIPT_DIR)
RELEASE_ZIP_LINK = "https://github.com/WojciechSobczak/build/archive/refs/tags/{}.zip"

def generate_setup_py(release_tag_name: str):
    with open(f"{SCRIPT_DIR}/setup.py", "r", encoding="UTF-8") as file:
        setup_py_text = file.read()

    setup_py_text = setup_py_text.replace(
        f'RELEASE_LINK = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"',
        f'RELEASE_LINK = "{RELEASE_ZIP_LINK.format(release_tag_name)}"'
    )
    setup_py_text = setup_py_text.replace(
        f'GITHUB_ZIP_PREFIX = "build-master/"', 
        f'GITHUB_ZIP_PREFIX = "build-{release_tag_name}/"'
    )

    os.makedirs(f"{SCRIPT_DIR}/releases/", exist_ok=True)
    release_file_path = f"{SCRIPT_DIR}/releases/setup.py"
    if os.path.exists(release_file_path):
        os.remove(release_file_path)
    with open(release_file_path, "w", encoding="UTF-8") as file:
        file.write(setup_py_text)

def fix_readme_links(release_tag_name: str):
    readme_file_path = f"{SCRIPT_DIR}/README.md"
    with open(readme_file_path, "r", encoding="UTF-8") as file:
        readme_text = file.read()
    readme_text = re.sub(
        r'https://github\.com/WojciechSobczak/build/releases/download/(.*)/setup\.py', 
        f'https://github.com/WojciechSobczak/build/releases/download/{release_tag_name}/setup.py', 
        readme_text
    )
    with open(readme_file_path, "w", encoding="UTF-8") as file:
        file.write(readme_text)
    
def generate_commit_messages_file():
    def _run(command: str): return commons.execute_command(command, cwd=SCRIPT_DIR, return_stdout=True) or ""
    branch_name = _run("git rev-parse --abbrev-ref HEAD")
    commits_list = _run(f"git cherry -v master {branch_name}")
    messages = []
    for commit in commits_list.splitlines():
        commit = commit[2:42]
        commit_text = _run(f"git log --format=%B -n 1 {commit}")
        messages.append(commit_text)
    messages_file_path = f"{SCRIPT_DIR}/releases/commit_messages.txt"
    with open(messages_file_path, "w", encoding="UTF-8") as file:
        for message in messages:
            file.write(message)

def main():
    parser = argparse.ArgumentParser(description="build_tools release utils")
    parser.add_argument('-v', '--version', default=None, type=str, help="Version string for release")
    parser.add_argument('-g', '--generate-setup', default=True, action='store_true', help="Generate setup.py for release")
    parser.add_argument('-r', '--readme-links-fix', default=True, help="Fix README.MD links")
    parser.add_argument('-m', '--commit-messages', default=True, help="Generate commit messages from branch")
    args = parser.parse_args()

    tag_name: str = args.version
    if tag_name is None:
        with open(f'{SCRIPT_DIR}/version.txt', "r", encoding="UTF-8") as file:
            tag_name = file.read().strip()
    else:
        with open(f'{SCRIPT_DIR}/version.txt', "w", encoding="UTF-8") as file:
            file.write(tag_name.strip())

    if args.generate_setup:
        generate_setup_py(tag_name)
    if args.readme_links_fix:
        fix_readme_links(tag_name)
    if args.commit_messages:
        generate_commit_messages_file()

if __name__ == "__main__":
    main()