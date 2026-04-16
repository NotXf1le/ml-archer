from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from ml_archer.shared.common import codex_home


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("bundle", help="Path to a .tar or .tar.zst bundle.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a prewarmed ml-archer formal bundle into the local cache.",
    )
    configure_parser(parser)
    return parser.parse_args()


def destination_root() -> Path:
    return codex_home() / "cache" / "ml-archer"


def _extract_bundle(bundle: Path, target_dir: Path) -> None:
    if bundle.suffixes[-2:] == [".tar", ".zst"]:
        zstd = shutil.which("zstd")
        if zstd is None:
            raise RuntimeError("Installing .tar.zst bundles requires the `zstd` executable.")
        tar_path = target_dir / "bundle.tar"
        subprocess.run([zstd, "-d", "-q", "-f", str(bundle), "-o", str(tar_path)], check=True)
        with tarfile.open(tar_path, "r") as archive:
            archive.extractall(target_dir)
        tar_path.unlink()
        return

    with tarfile.open(bundle, "r") as archive:
        archive.extractall(target_dir)


def install_bundle(bundle: Path) -> dict[str, object]:
    target_root = destination_root()
    target_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "bundle"
        extracted.mkdir(parents=True, exist_ok=True)
        _extract_bundle(bundle, extracted)

        shutil.copytree(extracted / "toolchains" / "home", target_root / "toolchains" / "home", dirs_exist_ok=True)
        shutil.copytree(extracted / "toolchains" / "elan", target_root / "toolchains" / "elan", dirs_exist_ok=True)
        shutil.copytree(
            extracted / "cache" / "shared_workspace",
            target_root / "shared_workspace",
            dirs_exist_ok=True,
        )

        manifest_path = extracted / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    return {
        "success": True,
        "bundle": str(bundle),
        "destination": str(target_root),
        "manifest": manifest,
    }


def main_from_args(args: argparse.Namespace) -> int:
    payload = install_bundle(Path(args.bundle).expanduser().resolve())
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    return main_from_args(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
