"""Entry point: parse args and run the chosen subcommand."""

import os
from datetime import date

import coloredlogs
from rendercv.schema.models.rendercv_model import RenderCVModel

from .app_params import (
    CvInputs,
    make_parser,
    parse_pdf_params,
    parse_typst_params,
    parse_web_params,
)
from .build_date import date_from_source_date_epoch
from .inputs import load_cv, load_website
from .logger import make_logger
from .pdf_builder import PdfBuilder
from .typst_renderer import render_typst
from .web_renderer import render_web

logger = make_logger(__name__)


def setup_logging(log_level: str, silent: bool) -> None:
    """Configure coloredlogs; silence all output when silent is set."""
    if silent:
        coloredlogs.install(level=10**6)
        return
    coloredlogs.install(
        level=log_level,
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def run(argv: list[str] | None = None) -> int:
    """Parse CLI args, run the chosen subcommand and return an exit code."""
    parser = make_parser()
    args = parser.parse_args(argv)
    setup_logging(args.log_level, args.silent)

    try:
        if args.subcommand == "typst":
            typst_params = parse_typst_params(args)
            render_typst(_load_model(typst_params.inputs), typst_params.output)

        elif args.subcommand == "pdf":
            pdf_params = parse_pdf_params(args)
            PdfBuilder(pdf_params.input, pdf_params.output).build()

        elif args.subcommand == "web":
            web_params = parse_web_params(args)
            model = _load_model(web_params.inputs)
            website = load_website(web_params.website, model.cv)
            render_web(model, website, web_params.template, web_params.output)

        return 0

    except Exception as e:
        logger.error("%s", e)
        return 1


def _load_model(inputs: CvInputs) -> RenderCVModel:
    return load_cv(
        inputs.cv,
        inputs.design,
        inputs.locale,
        inputs.settings,
        source_date=_source_date(),
    )


def _source_date() -> date | None:
    return date_from_source_date_epoch(os.environ.get("SOURCE_DATE_EPOCH"))
