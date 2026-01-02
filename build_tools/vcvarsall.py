import os
import urllib.request
import glob
import pickle

from . import commons
from . import log

def _get_vswhere_dir(workspace_dir: str):
    return f'{workspace_dir}/vswhere'

def _download_vswhere(workspace_dir: str) -> str:
    link = "https://github.com/microsoft/vswhere/releases/download/3.1.7/vswhere.exe"
    downloaded_exe = f'{_get_vswhere_dir(workspace_dir)}/vswhere.exe'
    os.makedirs(os.path.dirname(downloaded_exe), exist_ok=True)

    if not os.path.exists(downloaded_exe):
        log.info("Downloading vswhere executable...")
        urllib.request.urlretrieve(link, downloaded_exe)
        log.info("vswhere downloaded.")
    else:
        log.info("vswhere already present. Won't download.")
    return downloaded_exe


def _filter_out_vswhere_preamble(process_output: str) -> list[str]:
    # Format of vswhere output process is:
    # Preamble of VSWhere. Something like:
    #     Visual Studio Locator version 3.1.7+f39851e70f [query version 4.0.2113.32518]
    #     Copyright (C) Microsoft Corporation. All rights reserved.
    # And then data starts. First expected data row starts with
    #     instanceId: <something>
    # So this function filters whatever is before actual data
    first_data_index = 0
    process_text_lines = process_output.splitlines()
    for line in process_text_lines:
        if not line.startswith('instanceId:'):
            first_data_index += 1
        else:
            break
    return process_text_lines[first_data_index:]

def _parse_data_sections(data_lines: list[str]) -> list[list[str]]:
    # Now data.
    # So vswhere return rows in format like:
    # section_0_some_name: <data>
    # section_0_some_name_2: <data>
    # ...
    # <empty line>
    # section_1_some_name: <data>
    # section_1_some_name_2: <data>
    # ...

    data_sections: list[list[str]] = []
    current_data_section: list[str] = []
    for data_line in data_lines:
        if data_line == '':
            data_sections.append(current_data_section)
            current_data_section = []
        else:
            current_data_section.append(data_line)
    # Last section without empty line
    if len(current_data_section) > 0:
        data_sections.append(current_data_section)
    return data_sections

def _find_newest_version_installation_path(data_sections: list[list[str]]) -> tuple[str | None, str | None]:
    # Two interesting rows to be found
    # - resolvedInstallationPath - which is installation path of Visual Studio
    # - catalog_buildVersion - which is build version of said Visual Studio
    # Format of this version is just numbers with dots, so just merge them and compare them
    # Extract installation path from section, done.
    
    newest_version = "0.0.0"
    installation_path = None
    for data_section in data_sections:
        for row in data_section:
            if row.startswith('resolvedInstallationPath'):
                installation_path = row[row.find(':') + 1:].strip()
                continue
            if row.startswith('catalog_buildVersion'):
                version = row[row.find(':') + 1:].strip()
                for old_num, new_num in zip(newest_version.split('.'), version.split('.')):
                    if int(new_num) > int(old_num):
                        newest_version = version.strip()
                        break

    if newest_version == "0.0.0":
        log.warn("Cannot find 'catalog_buildVersion' in any of vswhere output text lines.")
    if installation_path is None:
        log.warn("Cannot find 'resolvedInstallationPath' in any of vswhere output text lines.")
    return (None, None) if newest_version == "0.0.0" else (newest_version, installation_path)

def _look_for_vcvarsall_in_vs_location(installation_path: str) -> str | None:
    file_names = glob.glob(f'{installation_path}/**/*', recursive=True)
    candidates = []
    for file_name in file_names:
        if os.path.basename(file_name) == 'vcvarsall.bat':
            candidates.append(file_name)
    if len(candidates) == 0:
        return None
    return commons.realpath(candidates[0])

def _apply_pickled_environment(file_path: str):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    if type(data) != dict:
        log.error(f"File '{file_path}' is corrupted. Remove it to load new one or replace it.")
        exit(-1)
    for key, value in data.items():
        if type(key) != str or type(value) != str:
            log.error(f"Data inside '{file_path}' is corrupted. Remove it to load new one or replace it.")
            exit(-1)
        os.environ[key] = value
    

def _pickle_and_save_environment(env_dict: dict[str, str], file_path: str):
    with open(file_path, 'wb') as file:
        pickle.dump(env_dict, file, protocol=pickle.HIGHEST_PROTOCOL)

def load_vcvarsall_env_if_possible(workspace_dir: str, project_dir: str) -> bool:
    if not commons.is_windows():
        log.warn("vcvarsall.bat can be only found on windows. Won't event try to do anything, as we are not on windows")
        return False
    
    CACHED_PICKLED_ENVIRONMENT_FILE = f"{_get_vswhere_dir(workspace_dir)}/CACHED_PICKLED_ENVIRONMENT_FILE.pickle"
    if os.path.exists(CACHED_PICKLED_ENVIRONMENT_FILE):
        log.info(f"Applying cached vcvarsall.bat output from cache: '{CACHED_PICKLED_ENVIRONMENT_FILE}'. Remove it manually if you want to refresh it.")
        _apply_pickled_environment(CACHED_PICKLED_ENVIRONMENT_FILE)
        return True

    downloaded_exe = _download_vswhere(workspace_dir)
    process_output = commons.execute_process([downloaded_exe], cwd=workspace_dir, return_stdout=True)
    if process_output is None or len(process_output) == 0:
        log.warn("vswhere.exe printed nothing. Cannot find vcvarsall and it won't be executed")
        return False

    data_lines = _filter_out_vswhere_preamble(process_output)
    data_sections = _parse_data_sections(data_lines)

    newest_version, installation_path = _find_newest_version_installation_path(data_sections)
    if newest_version is None or installation_path is None:
        log.warn("Cannot find version or path of VS. vcvarsall won't be executed")
        return False
    
    log.info(f"Looking for vsvarsall.bat of VS version: {newest_version} in '{installation_path}'...")
    vcvarsall_script_path = _look_for_vcvarsall_in_vs_location(installation_path)
    if vcvarsall_script_path is None:
        log.warn(f"Didn't find anything that is named 'vcvarsall.bat' inside '{installation_path}'. vcvarsall won't be executed")
        return False
    
    log.info(f"Found vsvarsall.bat in: {vcvarsall_script_path}. Executing...")
    after_execution_env_text = commons.execute_command(f'{vcvarsall_script_path} x64 > nul && SET', cwd=project_dir, return_stdout=True)
    if after_execution_env_text == None or len(after_execution_env_text) == 0:
        log.warn(f"There is no extracted text from after execution of vcvarsall.bat. No environment applied.")
        return False
    
    log.info(f"Extracting environment after vcvarsall.bat execution")
    env_lines = after_execution_env_text.splitlines()
    env_dict: dict[str, str] = {}
    for env_line in env_lines:
        eq_index = env_line.find('=')
        env_var_name, env_var_value = env_line[0 : eq_index], env_line[eq_index + 1:]
        env_dict[env_var_name] = env_var_value
        os.environ[env_var_name] = env_var_value
    log.info(f"Environment after vcvarsall.bat execution applied")
    log.info(f"Caching vcvarsall.bat execution environment in {CACHED_PICKLED_ENVIRONMENT_FILE}")
    _pickle_and_save_environment(env_dict, CACHED_PICKLED_ENVIRONMENT_FILE)
    return True