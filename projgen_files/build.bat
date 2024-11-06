SET script_name="${script_name}"
SET project_path="${project_path}"
python3 %script_name% -w %project_path% --package-manager="${package_manager}" %*