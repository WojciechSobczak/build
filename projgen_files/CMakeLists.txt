cmake_minimum_required(VERSION 3.20)
project(test)
set(CMAKE_CXX_STANDARD 20)

find_package(ctre CONFIG REQUIRED)
find_package(fmt REQUIRED)

add_executable(test "src/main.cpp")

target_link_libraries(test PRIVATE ctre::ctre)
target_link_libraries(test PRIVATE fmt::fmt)