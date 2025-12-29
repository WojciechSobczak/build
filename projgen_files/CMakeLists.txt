cmake_minimum_required(VERSION 4.2.0)
project(test C CXX)
set(CMAKE_CXX_STANDARD 23)

enable_language(ASM_NASM)
set(CAN_USE_ASSEMBLER TRUE)

find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(asio REQUIRED)
find_package(ctre CONFIG REQUIRED)
find_package(RapidJSON REQUIRED)

add_executable(${PROJECT_NAME} 
    "src/main.cpp" 
    "src/assembly.nasm"
)

target_link_libraries(${PROJECT_NAME} PRIVATE ctre::ctre)
target_link_libraries(${PROJECT_NAME} PRIVATE fmt::fmt)
target_link_libraries(${PROJECT_NAME} PRIVATE nlohmann_json::nlohmann_json)
target_link_libraries(${PROJECT_NAME} PRIVATE asio::asio)
target_link_libraries(${PROJECT_NAME} PRIVATE RapidJSON rapidjson)