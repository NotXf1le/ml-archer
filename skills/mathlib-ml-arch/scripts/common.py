from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


WINDOWS = os.name == "nt"


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is None or not hasattr(stream, "reconfigure"):
        return
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except ValueError:
        pass


def normalize_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return Path(path).expanduser().resolve()


def find_existing_proofs_root(start: str | Path | None = None) -> Path | None:
    anchor = normalize_path(start) or Path.cwd().resolve()
    for root in [anchor, *anchor.parents]:
        if (root / "proofs").is_dir():
            return root
    return None


def infer_workspace_root(start: str | Path | None = None) -> Path:
    return find_existing_proofs_root(start) or (normalize_path(start) or Path.cwd().resolve())


def derive_user_profile_from_tool(tool: Path | None) -> Path | None:
    if tool is None:
        return None

    parent = tool.parent
    while parent != parent.parent:
        if parent.name.lower() == ".elan":
            return parent.parent
        parent = parent.parent

    user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    return Path(user_profile).expanduser().resolve() if user_profile else None


def candidate_user_profiles() -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    raw_values = [
        os.environ.get("USERPROFILE"),
        os.environ.get("HOME"),
        str(Path.home()),
    ]

    for value in raw_values:
        if not value:
            continue
        path = Path(value).expanduser().resolve()
        if path not in seen:
            candidates.append(path)
            seen.add(path)

    if WINDOWS:
        users_dir = Path("C:/Users")
        if users_dir.exists():
            for child in sorted(users_dir.iterdir()):
                if child.is_dir() and child not in seen:
                    candidates.append(child)
                    seen.add(child)

    return candidates


def _winget_tool_candidates(tool_name: str) -> list[Path]:
    if not WINDOWS:
        return []

    relative_prefix = Path(
        "AppData/Local/Microsoft/WinGet/Packages/Lean.Lean_Microsoft.Winget.Source_8wekyb3d8bbwe"
    )
    matches: list[Path] = []
    for profile in candidate_user_profiles():
        base = profile / relative_prefix
        if not base.exists():
            continue
        for candidate in base.glob(f"lean-*-windows/bin/{tool_name}"):
            matches.append(candidate.resolve())
    return matches


def find_lake() -> Path | None:
    names = ["lake.exe", "lake"] if WINDOWS else ["lake"]
    for name in names:
        hit = shutil.which(name)
        if hit:
            return Path(hit).resolve()

    relative = Path(".elan/bin/lake.exe" if WINDOWS else ".elan/bin/lake")
    for profile in candidate_user_profiles():
        candidate = profile / relative
        if candidate.exists():
            return candidate.resolve()

    for candidate in _winget_tool_candidates("lake.exe"):
        if candidate.exists():
            return candidate

    return None


def find_lean(lake: Path | None = None) -> Path | None:
    names = ["lean.exe", "lean"] if WINDOWS else ["lean"]
    for name in names:
        hit = shutil.which(name)
        if hit:
            return Path(hit).resolve()

    if lake is not None:
        sibling = lake.with_name("lean.exe" if WINDOWS else "lean")
        if sibling.exists():
            return sibling.resolve()

    relative = Path(".elan/bin/lean.exe" if WINDOWS else ".elan/bin/lean")
    for profile in candidate_user_profiles():
        candidate = profile / relative
        if candidate.exists():
            return candidate.resolve()

    for candidate in _winget_tool_candidates("lean.exe"):
        if candidate.exists():
            return candidate

    return None


def subprocess_env_for_tool(tool: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if tool is not None:
        env["PATH"] = f"{tool.parent}{os.pathsep}{env.get('PATH', '')}"

    profile = derive_user_profile_from_tool(tool)
    if profile is not None:
        env["USERPROFILE"] = str(profile)
        env["HOME"] = str(profile)
        elan_home = profile / ".elan"
        if elan_home.exists():
            env["ELAN_HOME"] = str(elan_home)

    return env


def git_safe_directories_for_proofs(proofs_dir: Path) -> list[str]:
    directories: list[str] = []
    seen: set[str] = set()

    candidates = [proofs_dir]
    packages_dir = proofs_dir / ".lake" / "packages"
    if packages_dir.exists():
        candidates.extend(path for path in packages_dir.iterdir() if path.is_dir() and (path / ".git").exists())

    for candidate in candidates:
        value = candidate.resolve().as_posix()
        if value not in seen:
            directories.append(value)
            seen.add(value)

    return directories


def add_git_safe_directories(env: dict[str, str], directories: list[str]) -> dict[str, str]:
    if not directories:
        return env

    existing_count = 0
    try:
        existing_count = int(env.get("GIT_CONFIG_COUNT", "0"))
    except ValueError:
        existing_count = 0

    existing_values: set[str] = set()
    for index in range(existing_count):
        key = env.get(f"GIT_CONFIG_KEY_{index}")
        value = env.get(f"GIT_CONFIG_VALUE_{index}")
        if key == "safe.directory" and value:
            existing_values.add(value)

    additions = [directory for directory in directories if directory not in existing_values]
    if not additions:
        return env

    for offset, directory in enumerate(additions, start=existing_count):
        env[f"GIT_CONFIG_KEY_{offset}"] = "safe.directory"
        env[f"GIT_CONFIG_VALUE_{offset}"] = directory

    env["GIT_CONFIG_COUNT"] = str(existing_count + len(additions))
    return env


def discover_package_lib_dirs(proofs_dir: Path) -> list[Path]:
    candidates: list[Path] = []

    local_lib = proofs_dir / ".lake" / "build" / "lib" / "lean"
    if local_lib.exists():
        candidates.append(local_lib.resolve())

    packages_dir = proofs_dir / ".lake" / "packages"
    if packages_dir.exists():
        for package_dir in sorted(path for path in packages_dir.iterdir() if path.is_dir()):
            lib_dir = package_dir / ".lake" / "build" / "lib" / "lean"
            if lib_dir.exists():
                candidates.append(lib_dir.resolve())

    return candidates


def build_lean_path(proofs_dir: Path) -> str:
    return os.pathsep.join(str(path) for path in discover_package_lib_dirs(proofs_dir))


def default_project_name(workspace_root: Path) -> str:
    stem = workspace_root.name or "Workspace"
    parts = [part.capitalize() for part in stem.replace("-", " ").replace("_", " ").split() if part]
    return "".join(parts or ["Workspace"]) + "Proofs"
