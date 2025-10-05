"""Application module for the CV renderer package."""

import coloredlogs

from .app_params import AppParams, make_parser
from .logger import make_logger
from .renderer import CVRenderer

logger = make_logger(__name__)


def setup_logging(log_level: str, silent: bool) -> None:
    """Configure logging."""
    if silent:
        SILENT_LOG_LEVEL = 1000000
        coloredlogs.install(level=SILENT_LOG_LEVEL)
        return

    coloredlogs.install(
        level=log_level,
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    logger.debug(f"Logging set to {log_level}")


def run() -> int:
    """Run the application."""
    parser = make_parser()
    args = parser.parse_args()

    setup_logging(args.log_level, args.silent)

    try:
        app_params = AppParams(args)

        # Initialize renderer
        renderer = CVRenderer(templates_dir=app_params.templates_dir_path)

        # Load and validate data
        logger.info(f"Loading data from: {app_params.data_file_path}")
        cv_data = renderer.load_data(app_params.data_file_path)

        # Render templates
        for tp in app_params.templates:
            template_name = tp.template_file_path.name
            logger.info(f"Rendering CV using template: {template_name}")
            rendered = renderer.render(template_name, cv_data)

            output_file = tp.output_file_path
            if output_file:
                if not output_file.parent.exists():
                    logger.debug(f"Creating directory: {output_file.parent}")
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                file_mode = "w" if app_params.force else "x"

                logger.info(f"Writing rendered content to: {output_file}")
                with open(output_file, file_mode, encoding="utf-8") as f:
                    f.write(rendered)

            else:
                logger.info("Writing rendered content to stdout")
                print(rendered)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
