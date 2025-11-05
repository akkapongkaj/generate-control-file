#!/usr/bin/env python3
"""Generate control files for data extracts.

This script produces a control file that contains metadata about a data file.
The resulting control file follows the five-field pipe-delimited structure:

1. Processing/System date (YYYYMMDD)
2. Data date (YYYYMMDD)
3. Total number of data records
4. Data file name (with extension)
5. Checksum of the data file

The checksum algorithm defaults to MD5 to match legacy specifications, but
SHA-512 can also be used with the ``--checksum-algorithm`` flag.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
from pathlib import Path
from typing import Iterable


SUPPORTED_ALGORITHMS = {
    "md5": hashlib.md5,
    "sha512": hashlib.sha512,
}


def parse_date(value: str) -> str:
    """Validate and normalise a date string in YYYYMMDD format."""

    try:
        parsed = _dt.datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise argparse.ArgumentTypeError(
            "Dates must be provided in YYYYMMDD format"
        ) from exc

    return parsed.strftime("%Y%m%d")


def read_lines(path: Path) -> list[str]:
    """Read a file and return its lines without trailing newlines."""

    with path.open("r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def count_data_records(
    lines: Iterable[str], skip_header: int = 0, skip_footer: int = 0
) -> int:
    """Count the data records, excluding headers and footers.

    ``skip_header`` and ``skip_footer`` specify the number of lines to exclude
    from the start and end of the file, respectively. Blank lines are not
    counted as data records.
    """

    lines = list(lines)

    if skip_header:
        lines = lines[skip_header:]
    if skip_footer:
        lines = lines[: len(lines) - skip_footer]

    return sum(1 for line in lines if line.strip())


def calculate_checksum(path: Path, algorithm: str = "md5") -> str:
    """Calculate a checksum for ``path`` using ``algorithm``."""

    factory = SUPPORTED_ALGORITHMS.get(algorithm.lower())
    if factory is None:  # pragma: no cover - defensive guard
        raise ValueError(
            f"Unsupported checksum algorithm '{algorithm}'. "
            f"Choose one of: {', '.join(sorted(SUPPORTED_ALGORITHMS))}."
        )

    digest = factory()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_control_record(
    processing_date: str,
    data_date: str,
    record_count: int,
    data_file_name: str,
    checksum: str,
) -> str:
    """Assemble the pipe-delimited control record."""

    fields = [
        processing_date,
        data_date,
        str(record_count),
        data_file_name,
        checksum,
    ]
    return "|".join(fields)


def write_control_file(target: Path, record: str) -> None:
    """Write the control record to ``target`` with a trailing newline."""

    with target.open("w", encoding="utf-8") as handle:
        handle.write(record + "\n")


def generate_control_file(args: argparse.Namespace) -> Path:
    """Create the control file based on parsed CLI arguments."""

    data_path = Path(args.data_file).expanduser().resolve()
    if not data_path.is_file():
        raise FileNotFoundError(f"Data file '{data_path}' does not exist.")

    processing_date = parse_date(args.processing_date)
    data_date = parse_date(args.data_date or processing_date)

    lines = read_lines(data_path)
    record_count = count_data_records(
        lines,
        skip_header=args.skip_header,
        skip_footer=args.skip_footer,
    )
    checksum = calculate_checksum(data_path, args.checksum_algorithm)
    record = build_control_record(
        processing_date,
        data_date,
        record_count,
        data_path.name,
        checksum,
    )

    control_path = data_path.with_suffix(data_path.suffix + ".CTL")
    write_control_file(control_path, record)
    return control_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a control file for a data extract.",
    )
    parser.add_argument(
        "data_file",
        help="Path to the source data file (e.g. NCB_HPCHGREPOS.txt)",
    )
    parser.add_argument(
        "--processing-date",
        required=True,
        help="Processing/System date in YYYYMMDD format",
    )
    parser.add_argument(
        "--data-date",
        help="Data date in YYYYMMDD format (defaults to --processing-date)",
    )
    parser.add_argument(
        "--checksum-algorithm",
        choices=sorted(SUPPORTED_ALGORITHMS),
        default="md5",
        help="Checksum algorithm to use (default: md5)",
    )
    parser.add_argument(
        "--skip-header",
        type=int,
        default=0,
        help="Number of header lines to exclude from the record count",
    )
    parser.add_argument(
        "--skip-footer",
        type=int,
        default=0,
        help="Number of footer lines to exclude from the record count",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        control_path = generate_control_file(args)
    except Exception as exc:  # pragma: no cover - CLI guard
        parser.error(str(exc))

    print(f"Control file written to {control_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
