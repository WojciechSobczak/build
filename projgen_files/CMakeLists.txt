cmake_minimum_required(VERSION 4.2.0)
project(test C CXX)
set(CMAKE_CXX_STANDARD 23)

# Make this true if you want to use assembly
if (DEFINED MAKE_TRUE_IF_WANT_SOME_ASSEMBLY)
    enable_language(ASM_NASM)
    set(CAN_USE_ASSEMBLER TRUE)
    set(ASSEMBLY_SOURCES "src/assembly.nasm")
    add_compile_definitions(USE_ASSEMBLY)
endif()

find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(ctre CONFIG REQUIRED)
find_package(RapidJSON REQUIRED)

add_executable(${PROJECT_NAME} 
    "src/main.cpp" 
    ${ASSEMBLY_SOURCES}
)

target_link_libraries(${PROJECT_NAME} PRIVATE ctre::ctre)
target_link_libraries(${PROJECT_NAME} PRIVATE fmt::fmt)
target_link_libraries(${PROJECT_NAME} PRIVATE nlohmann_json::nlohmann_json)
target_link_libraries(${PROJECT_NAME} PRIVATE RapidJSON rapidjson)