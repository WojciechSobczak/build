import enum

class PackageManager(enum.Enum):
    CONAN = "conan",
    VCPKG = "vcpkg",
    ALL = "all"

    def __eq__(self, value):
        return self.value == value