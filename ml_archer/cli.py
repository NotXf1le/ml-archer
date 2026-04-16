from __future__ import annotations

import argparse
from typing import Sequence

from ml_archer.formal import doctor as formal_doctor
from ml_archer.formal import lean_check
from ml_archer.formal import search_mathlib
from ml_archer.formal import setup as formal_setup
from ml_archer.formal import validate_formal_bundle
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

    formal = subparsers.add_parser("formal", help="Explicit Lean/mathlib addon.")
    formal_subparsers = formal.add_subparsers(dest="formal_command", required=True)

    formal_doctor_parser = formal_subparsers.add_parser("doctor", help="Inspect formal addon readiness.")
    formal_doctor.configure_parser(formal_doctor_parser)
    formal_doctor_parser.set_defaults(handler=formal_doctor.main_from_args)

    formal_setup_parser = formal_subparsers.add_parser("setup", help="Prepare the formal addon workspace.")
    formal_setup.configure_parser(formal_setup_parser)
    formal_setup_parser.set_defaults(handler=formal_setup.main_from_args)

    formal_search_parser = formal_subparsers.add_parser("search", help="Search theorem candidates in mathlib.")
    search_mathlib.configure_parser(formal_search_parser)
    formal_search_parser.set_defaults(handler=search_mathlib.main_from_args)

    formal_check_parser = formal_subparsers.add_parser("check", help="Run Lean verification against ProofScratch.")
    lean_check.configure_parser(formal_check_parser)
    formal_check_parser.set_defaults(handler=lean_check.main_from_args)

    formal_validate_parser = formal_subparsers.add_parser(
        "validate-bundle",
        help="Validate a formal evidence bundle.",
    )
    validate_formal_bundle.configure_parser(formal_validate_parser)
    formal_validate_parser.set_defaults(handler=validate_formal_bundle.main_from_args)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler")
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
