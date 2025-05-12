import unittest
import commons
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

class ProjgenTest(unittest.TestCase):

    def recreate_test_dir(self, test_dir: str):
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        os.makedirs(test_dir, exist_ok=True)

    def test_conan_build(self):
        project_path = f'{SCRIPT_DIR}/tests/conan_build_test_dir'
        self.recreate_test_dir(project_path)
        try:
            commons.execute_command("python3 ../../build.py -w . --generate-project --conan", project_path)
            commons.execute_command("python3 build.py -dr -m debug", project_path)
            commons.execute_command("build -dr -m debug", project_path)
            self.assertTrue(True)
        except Exception as e:
            print(e)
            self.assertTrue(False)

    def test_vcpkg_build(self):
        project_path = f'{SCRIPT_DIR}/tests/vcpkg_build_test_dir'
        self.recreate_test_dir(project_path)
        try:
            commons.execute_command("python3 ../../build.py -w . --generate-project --package-manager=vcpkg", project_path)
            commons.execute_command("python3 build.py -dr -m debug", project_path)
            commons.execute_command("build -dr -m debug", project_path)
            self.assertTrue(True)
        except Exception as e:
            print(e)
            self.assertTrue(False)



