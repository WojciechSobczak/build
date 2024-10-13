# BUILD TOOLS 
Mini tools that provides easy setup of C++ CMake project with conan or vcpkg.


## Tutorial
* Clone this repo into your desired directory
* Make `build.py` accessible in path or run it directly from repo directory
* Use the mandatory `-w` parameter to set the directory that script will mess around in
* Enjoy


## Most interesting options
* `--package-manager` - either `conan` or `vcpkg`, if not set `conan` chosen by default
* `--generate-project` - creates simple project with dependencies configured. 
* `-r`, `--rebuild` - deletes cmake cache and rebuilds everything

Everything else is listed in `-h` option of `build.py`

## Example
* `cd your_directory`
* `git clone https://github.com/WojciechSobczak/build.git .`
* `python3 build.py -w <your_project_dir> --generate-project -d`
* `python3 build.py -w <your_project_dir> -r`


## License
Use it as you want. If you copy my code somewhere, you have to mention that its mine
in your final product for all to know that its mine and not yours.















