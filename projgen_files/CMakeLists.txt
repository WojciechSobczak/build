cmake_minimum_required(VERSION 3.20)
project(test C CXX)
set(CMAKE_CXX_STANDARD 20)

enable_language(ASM_NASM)
set(CAN_USE_ASSEMBLER TRUE)

find_package(ctre CONFIG REQUIRED)
find_package(fmt REQUIRED)

add_executable(test "src/main.cpp" "src/assembly.nasm")

target_link_libraries(test PRIVATE ctre::ctre)
target_link_libraries(test PRIVATE fmt::fmt)