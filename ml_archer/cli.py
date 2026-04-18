from __future__ import annotations

import argparse
from typing import Sequence

from ml_archer.tomography import validate_bundle as validate_tomography_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archer",
        description="ml-archer entrypoint for tomography-first ML architecture analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tomography = subparsers.add_parser("tomography", help="Typed architecture tomography utilities.")
    tomography_subparsers = tomography.add_subparsers(dest="tomography_command", required=True)
    tomography_validate = tomography_subparsers.add_parser(
        "validate",
        help="Validate a tomography bundle.",
    )
    validate_tomography_bundle.configure_parser(tomography_validate)
    tomography_validate.set_defaults(handler=validate_tomography_bundle.main_from_args)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler")
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
