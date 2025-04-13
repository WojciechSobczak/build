#include <fmt/format.h>
#include <ctre.hpp>
#include <nlohmann/json.hpp>

extern "C" {
    int assemblyFunction();
}

int main() {
    std::string helloWorld = "Hello World!";
    if (ctre::match<"Hello.*">(helloWorld)) {
        auto json = nlohmann::json::parse(R"({"Hello": "World"})");
        fmt::println("{}", json.dump());
    }
    return 0;
}