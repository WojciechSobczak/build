#include <fmt/format.h>
#include <ctre.hpp>

int main() {
    std::string helloWorld = "Hello World!";
    if (ctre::match<"Hello.*">(helloWorld)) {
        fmt::println("{}", helloWorld);
    }
    return 0;
}