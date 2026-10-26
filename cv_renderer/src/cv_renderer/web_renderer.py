"""Render the website files from the validated rendercv model."""

import traceback
from pathlib import Path

import jinja2
from rendercv.schema.models.rendercv_model import RenderCVModel

from .build_date import build_date
from .inputs import InputError
from .logger import make_logger
from .models import Website
from .template_utils import (
    as_list,
    date_range,
    markdown_inline,
    markdown_plain,
    phone_display,
    single_date,
    url_path,
)

logger = make_logger(__name__)


def make_web_environment(templates_dir: Path) -> jinja2.Environment:
    """Build the Jinja environment for the website templates.

    HTML and XML templates are autoescaped; JS and JSON templates aren't and
    use ``tojson`` instead.
    """
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=jinja2.select_autoescape(
            enabled_extensions=("html.j2", "xml.j2"), default_for_string=False
        ),
        undefined=jinja2.StrictUndefined,
    )
    # tojson writes pydantic URLs (HttpUrl) as strings
    environment.policies["json.dumps_kwargs"] = {"sort_keys": True, "default": str}
    environment.filters.update(
        as_list=as_list,
        markdown=markdown_inline,
        markdown_plain=markdown_plain,
        date_range=date_range,
        single_date=single_date,
        phone_display=phone_display,
    )
    environment.globals["url_path"] = url_path
    return environment


def render_web(
    model: RenderCVModel, website: Website, template: Path, output: Path
) -> None:
    """Render template with the CV model and website, and write output."""
    environment = make_web_environment(template.parent)
    try:
        content = environment.get_template(template.name).render(
            cv=model.cv,
            design=model.design,
            locale=model.locale,
            website=website,
            build_date=build_date(model),
        )
    except jinja2.TemplateNotFound as e:
        raise InputError(f"{template}: template not found") from e
    except jinja2.TemplateSyntaxError as e:
        raise InputError(f"{template}:{e.lineno}: {e.message}") from e
    except jinja2.TemplateError as e:
        raise InputError(f"{_location(template, e)}: {e}") from e
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    logger.info("Written: %s", output)


def _location(template: Path, error: Exception) -> str:
    # Jinja rewrites tracebacks so that template frames point at template lines
    frames = traceback.extract_tb(error.__traceback__)
    lines = [f.lineno for f in frames if f.filename == str(template) and f.lineno]
    return f"{template}:{lines[-1]}" if lines else str(template)
