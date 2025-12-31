import os
import sys
import re
import platform
import subprocess
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")

def main():
    TEST_PROJECT_DIR = f"{SCRIPT_DIR}/tests/{platform.system()}/"
    TEST_BUILD_TOOLS_DIR = f"{TEST_PROJECT_DIR}/.workspace/build_tools"

    with open(f"{SCRIPT_DIR}/setup.py", "r", encoding="UTF-8") as file:
        text = file.read()
        regexp = re.compile(r'(os\.makedirs\(workspace_folder, exist_ok=True\)).*|\s(os\.remove\(zip_path\))')
        matches = list(regexp.finditer(text))

        remove_start_pos = matches[0].span()[0]
        remove_end_pos = matches[1].span()[1]
        text = ''.join([
            text[0:remove_start_pos],
            textwrap.indent(textwrap.dedent(f"""
                def _test_copy_files():
                    files = os.listdir("{SCRIPT_DIR}")
                    for file in files:
                        if file.endswith('.py'):
                            shutil.copy(f'{SCRIPT_DIR}/{{file}}', f'{TEST_BUILD_TOOLS_DIR}/{{file}}')
                _test_copy_files()
            """), "    "),
            text[remove_end_pos + 1:]
        ])

        text = text.replace('projgen_files = f"{extract_path}/projgen_files"', f'projgen_files = f"{SCRIPT_DIR}/projgen_files"')

    os.makedirs(TEST_BUILD_TOOLS_DIR, exist_ok=True)
    with open(f"{TEST_BUILD_TOOLS_DIR}/setup.py", "w", encoding="UTF-8") as file:
        file.write(text)
    with open(f"{TEST_PROJECT_DIR}/setup.py", "w", encoding="UTF-8") as file:
        file.write(text)

    def _run_or_die(args: list[str]):
        process = subprocess.run(args=args, cwd = TEST_PROJECT_DIR)
        if process.returncode != 0:
            sys.exit(f'FAIL: args=f{args}')

    _run_or_die(["python3", "setup.py", "-g"])
    _run_or_die(["python3", "build.py", "-d", "-m", "debug"])
    _run_or_die(["python3", "build.py", "-d", "-m", "release"])
    _run_or_die(["python3", "build.py", "-c", "-m", "debug"])
    _run_or_die(["python3", "build.py", "-c", "-m", "release"])
    _run_or_die(["python3", "build.py", "-r", "-m", "debug"])
    _run_or_die(["python3", "build.py", "-r", "-m", "release"])
    _run_or_die(["python3", "build.py", "--clion"])

if __name__ == "__main__":
    main()