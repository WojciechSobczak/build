import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")

def main():
    RELEASE_LINK = "https://github.com/WojciechSobczak/build/archive/{}.zip"
    git_hash = subprocess.run(args=["git", "rev-parse", "HEAD"], cwd = SCRIPT_DIR, stdout=subprocess.PIPE).stdout.decode("utf-8").strip()

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