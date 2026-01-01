import dataclasses

@dataclasses.dataclass(frozen=True)
class BuildToolsConfig:
    cmake_exe: str
    conan_exe: str | None
    vcpkg_exe: str | None
    ninja_exe: str | None
    workspace_dir: str
    project_dir: str
    build_mode: str

    def is_ninja_set(self) -> bool:
        return self.ninja_exe is not None