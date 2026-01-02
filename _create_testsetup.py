import argparse
import os
import re
import platform
import textwrap
from build_tools import commons

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
TEST_PROJECT_DIR = f"{SCRIPT_DIR}/tests/{platform.system()}/"
TEST_BUILD_TOOLS_DIR = f"{TEST_PROJECT_DIR}/.workspace/build_tools"

def generate_setups_and_copy():
    with open(f"{SCRIPT_DIR}/setup.py", "r", encoding="UTF-8") as file:
        setup_py_text = file.read()

    download_text_replace_regexp = re.compile(r'(#START).*|\s(#END.*)')
    matches = list(download_text_replace_regexp.finditer(setup_py_text))

    remove_start_pos = matches[0].span()[1]
    remove_end_pos = matches[1].span()[0]
    setup_py_text = ''.join([
        setup_py_text[0:remove_start_pos],
        textwrap.indent(textwrap.dedent(f"""
            def _test_copy_files():
                src_projgen_dir = '{SCRIPT_DIR}/build_tools/projgen_files'
                src_pyfiles_dir = os.path.dirname(src_projgen_dir)
                dst_projgen_dir = '{TEST_BUILD_TOOLS_DIR}/build_tools/projgen_files'
                dst_pyfiles_dir = os.path.dirname(dst_projgen_dir)
                os.makedirs(dst_projgen_dir, exist_ok=True)

                py_files = [f for f in os.listdir(src_pyfiles_dir) if os.path.isfile(f'{{src_pyfiles_dir}}/{{f}}')]
                for file in py_files:
                    shutil.copy(f'{{src_pyfiles_dir}}/{{file}}', f'{{dst_pyfiles_dir}}/{{file}}')
                projgen_files = [f for f in os.listdir(src_projgen_dir) if os.path.isfile(f'{{src_projgen_dir}}/{{f}}')]
                for file in projgen_files:
                    shutil.copy(f'{{src_projgen_dir}}/{{file}}', f'{{dst_projgen_dir}}/{{file}}')
                build_file_template_src_path = f'{{os.path.dirname(src_pyfiles_dir)}}/build_user_file.py'
                build_file_template_dst_path = f'{{os.path.dirname(dst_pyfiles_dir)}}/build_user_file.py'
                shutil.copy(build_file_template_src_path, build_file_template_dst_path)
            _test_copy_files()
        """), "    "),
        setup_py_text[remove_end_pos + 1:]
    ])
    setup_py_text = setup_py_text.replace('projgen_files = f"{extract_path}/build_tools/projgen_files"', f'projgen_files = f"{SCRIPT_DIR}/build_tools/projgen_files"')

    os.makedirs(TEST_BUILD_TOOLS_DIR, exist_ok=True)
    with open(f"{TEST_BUILD_TOOLS_DIR}/setup.py", "w", encoding="UTF-8") as file:
        file.write(setup_py_text)
    with open(f"{TEST_PROJECT_DIR}/setup.py", "w", encoding="UTF-8") as file:
        file.write(setup_py_text)

def main():
    parser = argparse.ArgumentParser(description="build_tools test utils")
    parser.add_argument('-ns', '--no-setup', default=False, action='store_true', help="Don't generate setup.py")
    parser.add_argument('-f', '--fresh-test-env', default=False, action='store_true', help="Delete all test files")
    args = parser.parse_args()

    if args.fresh_test_env and os.path.exists(TEST_PROJECT_DIR):
        commons.delete_dir(TEST_PROJECT_DIR)
    if not args.no_setup:
        os.makedirs(TEST_PROJECT_DIR, exist_ok=True)
        generate_setups_and_copy()

    def _run(args: list[str]):
        commons.execute_process(args, cwd=TEST_PROJECT_DIR)

    # Setup
    _run(["python3", "setup.py", "-g", "-o"])

    # Build debug
    _run(["python3", "build.py", "-d", "-m", "debug"])
    _run(["python3", "build.py", "-c", "-m", "debug"])
    _run(["python3", "build.py", "-r", "-m", "debug"])

    # Build release
    _run(["python3", "build.py", "-d", "-m", "release"])
    _run(["python3", "build.py", "-c", "-m", "release"])
    _run(["python3", "build.py", "-r", "-m", "release"])

    # Addons
    _run(["python3", "build.py", "--clion"])

if __name__ == "__main__":
    main()