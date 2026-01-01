import os, sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
if "PYTHONPATH" not in os.environ: os.environ["PYTHONPATH"] = ""
os.environ["PYTHONPATH"] = f'$PYTHONPATH{os.pathsep}{SCRIPT_DIR}'
sys.path.append(SCRIPT_DIR)

import build_tools

def main():
    RELEASE_LINK = "https://github.com/WojciechSobczak/build/archive/{}.zip"

    git_hash = build_tools.commons.execute_process(["git", "rev-parse", "HEAD"], SCRIPT_DIR, return_stdout=True).strip()

    with open(f"{SCRIPT_DIR}/setup.py", "r", encoding="UTF-8") as file:
        text = file.read()
        text = text.replace(
            f'RELEASE_LINK = "https://github.com/WojciechSobczak/build/archive/refs/heads/master.zip"',
            f'RELEASE_LINK = "{RELEASE_LINK.format(git_hash)}"'
        )
        text = text.replace(
            f'GITHUB_ZIP_PREFIX = "build-master/"', 
            f'GITHUB_ZIP_PREFIX = "build-{git_hash}/"'
        )

        os.makedirs(f"{SCRIPT_DIR}/releases/", exist_ok=True)
        release_file_path = f"{SCRIPT_DIR}/releases/setup.py"
        if os.path.exists(release_file_path):
            os.remove(release_file_path)
        with open(release_file_path, "w", encoding="UTF-8") as file:
            file.write(text)

if __name__ == "__main__":
    main()