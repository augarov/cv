"""
Application parameters module for the CV renderer package.

This module provides the application parameters parsing functionality.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

from .logger import make_logger

logger = make_logger(__name__)


def make_parser() -> argparse.ArgumentParser:
    """Make parser for the application."""
    parser = argparse.ArgumentParser(
        prog="cv_renderer",
        description="Render CV from YAML data using Jinja2 templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d cv_data.yaml templates/cv.tex.j2 cv.tex
        """,
    )

    parser.add_argument(
        "--data",
        "-d",
        required=True,
        help="YAML data file path",
    )

    parser.add_argument(
        "--input",
        "-i",
        nargs="+",
        help="Input template file path(s)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output path, writes to stdout if not provided",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing output file",
    )

    parser.add_argument(
        "--log-level",
        "-l",
        default="INFO",
        help="Log level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Silent mode, no logging",
    )

    return parser


@dataclass
class TemplateParams:
    """Input template parameters."""

    template_file_path: Path
    output_file_path: Path | None


class AppParams:
    """Application parameters."""

    def __init__(self, args: argparse.Namespace):
        """
        Initialize application parameters. Parses and validates application arguments.

        Args:
            args: Application arguments.
        """
        self.data_file_path = _parse_file_path(args.data)
        self.templates = _parse_templates(args)
        self.templates_dir_path = self.templates[0].template_file_path.parent
        self.force = args.force

        input_files = {self.data_file_path}

        for tp in self.templates:
            inp = tp.template_file_path
            if inp in input_files:
                raise ValueError(f"Same input file path {inp} is used multiple times")

            input_files.add(inp)

            if out := tp.output_file_path:
                if out in input_files:
                    raise ValueError(
                        f"Output file path '{out}' is also used as an input file path, "
                        "cannot overwrite input file"
                    )

                if out.is_relative_to(self.templates_dir_path):
                    raise ValueError(
                        f"Cannot save output file '{out}' to the templates directory"
                    )

                existing_predecessor = out.parent
                while not existing_predecessor.exists():
                    existing_predecessor = existing_predecessor.parent

                if not existing_predecessor.is_dir():
                    raise ValueError(
                        f"Cannot save output file to '{out}', "
                        f"'{existing_predecessor}' is not a directory"
                    )

            if inp.parent != self.templates_dir_path:
                raise ValueError(
                    f"Input template path '{inp}' is not in the templates directory"
                )


def _file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _ensure_file_exists(path: Path) -> None:
    if not _file_exists(path):
        raise FileNotFoundError(f"File '{path}' not found")


def _parse_file_path(arg: str) -> Path:
    path = Path(arg).resolve()
    _ensure_file_exists(path)
    return path


def _parse_templates(args: argparse.Namespace) -> list[TemplateParams]:
    template_params = _parse_template_params(args)

    for template_param in template_params:
        inp = template_param.template_file_path
        _ensure_file_exists(inp)

        if out := template_param.output_file_path:
            logger.debug(f"Output for template {inp} will be saved to {out}")
            if out.exists():
                if args.force:
                    if not out.is_file():
                        raise FileExistsError(
                            f"Path '{out}' already exists and is not a file, "
                            "cannot overwrite"
                        )
                    logger.warning(f"Path '{out}' already exists, " "overwriting")
                else:
                    raise FileExistsError(
                        f"Path '{out}' already exists, " "use --force to overwrite"
                    )
        else:
            logger.debug(f"Output for template {inp} will be saved to stdout")

    return template_params


def _parse_template_params(args: argparse.Namespace) -> list[TemplateParams]:

    if len(args.input) == 1:
        return [_parse_single_template_params(args.input[0], args.output)]

    return _parse_multiple_template_params(args.input, args.output)


def _parse_single_template_params(
    template_arg: str, output_arg: str | None
) -> TemplateParams:
    logger.debug("Single input template file")

    template_path = _parse_file_path(template_arg)

    if output_arg is None:
        logger.info("Output path not provided, writing to stdout")
        return TemplateParams(template_file_path=template_path, output_file_path=None)

    output_path = Path(output_arg).resolve()
    if output_path.is_dir():
        output_path = output_path / _make_output_file_name(template_path)
    return TemplateParams(
        template_file_path=template_path, output_file_path=output_path
    )


def _parse_multiple_template_params(
    template_args: list[str], output_arg: str | None
) -> list[TemplateParams]:
    logger.debug("Multiple input template files")

    if output_arg is None:
        raise ValueError(
            "For multiple input template files, output path must be provided"
        )

    output_dir = Path(output_arg).resolve()
    if not output_dir.is_dir():
        raise ValueError(
            "For multiple input template files, output path must be a directory"
        )

    logger.debug(f"Output directory: {output_dir}")

    template_params = []
    for template_arg in template_args:
        template_path = _parse_file_path(template_arg)
        output_path = output_dir / _make_output_file_name(template_path)
        template_params.append(
            TemplateParams(
                template_file_path=template_path, output_file_path=output_path
            )
        )

    return template_params


def _make_output_file_name(template_path: Path) -> str:
    """Make output file name from template path."""
    if template_path.name.endswith(".j2"):
        return template_path.name[:-3]

    return template_path.name
