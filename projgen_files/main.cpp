#include <fmt/format.h>
#include <ctre.hpp>
#include <nlohmann/json.hpp>
#include <rapidjson/document.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

//Remove if you dont use assembly
#ifdef USE_ASSEMBLY
extern "C" {
    int assemblyFunction();
}
#endif

int main() {
    std::string helloWorld = "Hello World!";
    if (ctre::match<"Hello.*">(helloWorld)) {
        auto json = nlohmann::json::parse(R"({"Hello": "nlohmann::json"})");
        fmt::println("nlohmann::json {}", json.dump());

        // Read and parse the file
        rapidjson::Document document;
        document.Parse<0>(R"({"Hello": "rapidjson::Document"})");

        rapidjson::StringBuffer buffer;
        rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
        document.Accept(writer);
        fmt::println("rapidjson::Document {}", buffer.GetString());
    }

//Remove if you dont use assembly
#ifdef USE_ASSEMBLY
    fmt::println("Assembly gave us: {}", assemblyFunction());
#endif

    return 0;
}