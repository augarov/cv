"""CLI argument parsing for cv_renderer subcommands."""

import argparse
from dataclasses import dataclass
from pathlib import Path


def make_parser() -> argparse.ArgumentParser:
    """Build the argument parser with the typst, pdf and web subcommands."""
    parser = argparse.ArgumentParser(
        prog="cv_renderer",
        description="Render a rendercv CV to Typst, PDF and website files",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--silent", "-s", action="store_true")

    # rendercv's inputs, shared by typst and web so the two can't drift apart
    cv_inputs = argparse.ArgumentParser(add_help=False)
    cv_inputs.add_argument("--cv", required=True, type=Path, metavar="PATH")
    cv_inputs.add_argument("--design", type=Path, metavar="PATH")
    cv_inputs.add_argument("--locale", type=Path, metavar="PATH")
    cv_inputs.add_argument("--settings", type=Path, metavar="PATH")

    sub = parser.add_subparsers(dest="subcommand", required=True)

    # ── typst ───────────────────────────────────────────────────────────────
    typst = sub.add_parser(
        "typst",
        parents=[cv_inputs],
        help="Render the Typst source of the PDF (theme from design.yaml)",
    )
    typst.add_argument("--output", "-o", required=True, type=Path, metavar="PATH")

    # ── pdf ─────────────────────────────────────────────────────────────────
    pdf = sub.add_parser("pdf", help="Compile a rendered .typ file to PDF")
    pdf.add_argument("--input", "-i", required=True, type=Path, metavar="PATH")
    pdf.add_argument("--output", "-o", required=True, type=Path, metavar="PATH")

    # ── web ─────────────────────────────────────────────────────────────────
    web = sub.add_parser(
        "web",
        parents=[cv_inputs],
        help="Render a website template with the CV and website.yaml",
    )
    web.add_argument("--website", required=True, type=Path, metavar="PATH")
    web.add_argument("--template", required=True, type=Path, metavar="PATH")
    web.add_argument("--output", "-o", required=True, type=Path, metavar="PATH")

    return parser


@dataclass(frozen=True)
class CvInputs:
    """rendercv's input files; only cv is required."""

    cv: Path
    design: Path | None
    locale: Path | None
    settings: Path | None


@dataclass(frozen=True)
class TypstParams:
    """Arguments of the typst subcommand."""

    inputs: CvInputs
    output: Path


@dataclass(frozen=True)
class PdfParams:
    """Arguments of the pdf subcommand."""

    input: Path
    output: Path


@dataclass(frozen=True)
class WebParams:
    """Arguments of the web subcommand."""

    inputs: CvInputs
    website: Path
    template: Path
    output: Path


def parse_typst_params(args: argparse.Namespace) -> TypstParams:
    """Convert parsed args of the typst subcommand."""
    return TypstParams(inputs=_cv_inputs(args), output=args.output)


def parse_pdf_params(args: argparse.Namespace) -> PdfParams:
    """Convert parsed args of the pdf subcommand."""
    return PdfParams(input=args.input, output=args.output)


def parse_web_params(args: argparse.Namespace) -> WebParams:
    """Convert parsed args of the web subcommand."""
    return WebParams(
        inputs=_cv_inputs(args),
        website=args.website,
        template=args.template,
        output=args.output,
    )


def _cv_inputs(args: argparse.Namespace) -> CvInputs:
    return CvInputs(
        cv=args.cv, design=args.design, locale=args.locale, settings=args.settings
    )
