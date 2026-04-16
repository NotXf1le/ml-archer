from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ml_archer.shared.common import codex_home, mathlib_revision_for_toolchain, normalize_lean_toolchain


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output",
        default="dist",
        help="Output directory for the bundle artifact.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a prewarmed ml-archer formal bundle from the local cache.",
    )
    configure_parser(parser)
    return parser.parse_args()


def cache_root() -> Path:
    return codex_home() / "cache" / "ml-archer"


def bundle_name(toolchain: str | None, mathlib_rev: str | None) -> str:
    toolchain_part = (toolchain or "unknown").replace("leanprover/lean4:", "").replace("/", "-")
    mathlib_part = mathlib_rev or "unknown"
    return (
        f"ml-archer-formal-{platform.system().lower()}-{platform.machine().lower()}"
        f"-lean4-{toolchain_part}-mathlib-{mathlib_part}"
    )


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(root: Path) -> None:
    lines: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "checksums.txt":
            continue
        lines.append(f"{sha256_for(path)}  {relative}")
    (root / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_manifest(staging_root: Path) -> dict[str, object]:
    proofs_dir = staging_root / "cache" / "shared_workspace" / "proofs"
    toolchain = normalize_lean_toolchain((proofs_dir / "lean-toolchain").read_text(encoding="utf-8").strip())
    mathlib_rev = mathlib_revision_for_toolchain(toolchain)
    manifest = {
        "bundle_format": 1,
        "product": "ml-archer",
        "plugin_slug": "ml-archer",
        "toolchain": f"leanprover/lean4:{toolchain}" if toolchain else None,
        "mathlib_rev": mathlib_rev,
        "os": platform.system().lower(),
        "arch": platform.machine().lower(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paths": {
            "tool_home": "toolchains/home",
            "elan_home": "toolchains/elan",
            "shared_workspace": "cache/shared_workspace",
        },
    }
    (staging_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def prepare_staging(staging_root: Path) -> dict[str, object]:
    source_root = cache_root()
    toolchains_root = source_root / "toolchains"
    shared_root = source_root / "shared_workspace"
    if not toolchains_root.exists() or not shared_root.exists():
        raise FileNotFoundError("Formal cache is incomplete. Run formal setup before building a bundle.")

    target_toolchains = staging_root / "toolchains"
    target_cache = staging_root / "cache" / "shared_workspace"
    shutil.copytree(toolchains_root / "home", target_toolchains / "home", dirs_exist_ok=True)
    shutil.copytree(toolchains_root / "elan", target_toolchains / "elan", dirs_exist_ok=True)
    shutil.copytree(shared_root, target_cache, dirs_exist_ok=True)
    manifest = create_manifest(staging_root)
    write_checksums(staging_root)
    return manifest


def archive_staging(staging_root: Path, output_dir: Path, artifact_stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    tar_path = output_dir / f"{artifact_stem}.tar"
    with tarfile.open(tar_path, "w") as archive:
        archive.add(staging_root, arcname=".")

    zstd = shutil.which("zstd")
    if zstd is None:
        return tar_path

    zst_path = output_dir / f"{artifact_stem}.tar.zst"
    subprocess.run([zstd, "-q", "-f", str(tar_path), "-o", str(zst_path)], check=True)
    tar_path.unlink()
    return zst_path


def main_from_args(args: argparse.Namespace) -> int:
    output_dir = Path(args.output).expanduser().resolve()
    with tempfile.TemporaryDirectory() as tmp:
        staging_root = Path(tmp)
        manifest = prepare_staging(staging_root)
        artifact_stem = bundle_name(manifest.get("toolchain"), manifest.get("mathlib_rev"))
        artifact_path = archive_staging(staging_root, output_dir, artifact_stem)
    print(
        json.dumps(
            {
                "success": True,
                "artifact": str(artifact_path),
                "output_dir": str(output_dir),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    return main_from_args(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
