import argparse
from pathlib import Path

from pydantic import ValidationError
from ocr.config.settings import Settings 

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        type=str,
        help="LLM name in `litellm` supported format."
    )
    parser.add_argument(
        "--pdf-path",
        type=Path,
        help="Path to the input PDF diagram file."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature setting for an LLM."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        help="DPI setting for PDF to PNG conversion."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of PDF pages (PNGs) processed by LLM per batch."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Path to the output folder."
    )
    return parser.parse_args()

def main() -> int:

    args: argparse.Namespace = parse_args()
    overrides = {k: v for k, v in vars(args).items() if v is not None}

    try:
        settings = Settings(**overrides)
    except ValidationError:
        # Some console log should be there
        raise
    print(settings.model_dump_json(indent=4))
    # Some success console log should be there
    return 0


if __name__ == "__main__":
    raise SystemExit(main())