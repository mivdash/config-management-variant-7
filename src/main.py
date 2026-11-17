"""Командная строка конвертера варианта 7."""

import argparse
import sys
from pathlib import Path

from converter import convert

FAILURE = 1
SUCCESS = 0


def main():
    """Читает входной файл UTF-8 и выводит результат или диагностику."""
    parser = argparse.ArgumentParser(description="Конвертер варианта 7 в TOML")
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="входной файл UTF-8"
    )
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parser.parse_args()
    try:
        result = convert(args.input.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        print(f"{args.input}: {error}", file=sys.stderr)
        return FAILURE
    print(result, end="")
    return SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
