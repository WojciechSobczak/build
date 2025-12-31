# BUILD TOOLS 
My personal C++ project setup tool, to overcome pain in the ass of making C++ projects usable and easy to start.  
Goal of if it is to create 'just works' conan based project creation and building toolset with additional custom dependencies with vcpkg on the side as an addition, as conan doesn't have everything. Note that vcpkg is an addition, tested on things that were tested and not everything has to work, but majority should. As I said. Conan based, vcpkg as an addition. It setups all tools needed, all dependencies needed and just builds project for you to enjoy coding instead of fighting with toolchains and package managers.

It contains all libraries that I consider most useful and `rapidjson` to be sure that vcpkg is working. This list of libraries will evolve so don't hesitate to remove everything you don't need before running the dependencies downloading process.

## Prerequisites
For everything to work you have to have `python3` installed, as every script in this repo is made in python. No additional libraries required. Only python standard library. This project is tested on Windows 11 and WSL within it. It isn't complicated, so it should work on 10 and native linuxes, but there is no guarantee. If there would be problems, let me know via github issues, I'll probably try to resolve it somehow. 

As this tool doesn't provide any compilers and c++ build tools beside ninja and cmake, you have to have some compiler installed.
For windows the easiest option is to install Visual Studio and it will add everything to your environment. If you want something else, you have to setup it yourself.
At some point I'll add compilers and build tools to make the process easier and more portable.
For linux of course, as on windows, some compiler needs to be setup for cmake to find it.

## Tutorial
To start a project you have to somehow get `setup.py` file and run it with `python3` wherever you want to create your project. You can download it via github manually or use some kind of downloader to get it. This is entirely up to you. You have to just get it and run it. 

### What does it do?
`setup.py` is doing three things:
- creating workspace folder for the project (default name for it is `.workspace`)
- downloading build_tools project for everything to work 
- generating project files, which are:
  - `CMakeLists.txt` - cmake project file
  - `conanfile.txt` - conan dependencies file
  - `vcpkg.json` - vcpkg dependencies file
  - `src/main.cpp` - C++ code main file
  - `src/assembly.nasm` - additional, if you want, nasm assembly file
  - `build.py` - build_tools build script for the project

After running it and after it ends its doings, you can safely delete it, as it won't be needed anymore. Everything you need, you got from now. 

### Command line of `setup.py`
`setup.py` has some arguments that you can customize your project creation with.
- `-g` or `--generate-project` - which tells it if it has to copy and paste initial. It is `False` by default.
project files
- `-w` or `--workspace-name` - which tells it how the project workspace folder has to be named. It will be placed 
inside the directory where script were downloaded. It is `.workspace` by default.

### Usage Examples
Note: I highly recommend using releases `setup.py` links as they have their commit hash embedded in them, so every recreation of build_tools
files if needed, will be created from very specific version that you started working with and works.


On windows if you have `powershell` you can use following command:
- `Invoke-WebRequest https://raw.githubusercontent.com/WojciechSobczak/build/refs/heads/master/setup.py -OutFile setup.py; python3 setup.py;`

Which will download the newest `setup.py` and execute it, creating new project. 

If you are stuck to `cmd` or `bash` on linux you have to use whatever you have available. If you have `curl` you can use it like:

`curl --output setup.py https://raw.githubusercontent.com/WojciechSobczak/build/refs/heads/master/setup.py && python3 setup.py`

Or if you have `wget`:

`wget https://raw.githubusercontent.com/WojciechSobczak/build/refs/heads/master/setup.py && python3 setup.py`


## `build.py`
`build.py` is most important creation of this project as it is tool that will build stuff.  
It is entirely up to you what you'll do with it. It provides basics that are convenient enough for me and what I decided to be the most useful things to have. It builds, it rebuilds, it configures cmake.  
There are options listed inside it and they will change as additions will be introduced, but the baseline for now is:  
- `-c` or `--config`- run `cmake` configuration (default = `False`)
- `-b` or `--build` - run `cmake` build (default = `False`)
- `-r` or `--rebuild` - delete `cmake` cache and run `cmake` build (default = `False`)
- `-m` or `--mode` - set `cmake` build type. You can set whatever, string will be passed around and if some tool won't recognize it, it will just fail. (default=`debug`)
- `-d` or `--dependencies` - downloads dependencies from conan and vcpkg if present. It setups conan profiles as well. (default = `False`)
- `--clion` - creates CLion default CMake configurations (as XML files; Debug, Release; in `.idea` folder) for the project with all CMake paths, generators and variables set. Additionaly it adds some dictionary to remove spell checking errors for some words that are used in templates. It's made to easy run the project on CLion IDE with no mouse clicking if possible. Be aware that cmake executable cannot be set, so it's the only thing you'll have to click by yourself. Warning will be displayed. (default = `False`)

As I mentioned before, this file is a playground. Is commented for you to see how to customize it for your needs. Change it, ruin it, modify it. It is supposed to be created once and be used for entirety of the lifetime of the project. For now it is able to download and use:
- `conan` 
- `cmake`
- `ninja`
- `vcpkg`
  
It will download it to the workspace directory and use it without need of having them installed before. If you have them installed, `build.py` have the option to use it, find it, uncomment it, and use it. All dependencies are installed locally inside workspace directory as well. It is by design, I like it, it won't change.

`build.py` will at the beginning check if build tools are present in workspace directory, so once performed, there is no need to repeat the procedure of setup.


## License
Use it as you want. If you copy my code somewhere, you have to mention that its mine
for all to know that its mine and not yours. You are not allowed to use it commercially unless i agree to it.


