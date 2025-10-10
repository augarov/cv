"""
Renderer module for CV rendering.

Core CV rendering functionality using Jinja2 templates with AST-based
markdown processing.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .ast import (
    ASTToHTMLRenderer,
    ASTToLaTeXRenderer,
    ASTToPlainRenderer,
    escape_html_text,
    escape_latex_text,
)
from .logger import make_logger
from .models import CVData
from .template_type import TemplateType
from .template_utils import (
    format_current_time,
    normalize_url,
    url_path,
    wrap_in_double_quotes,
)

logger = make_logger(__name__)


class CVRenderer:
    """CV Renderer using Jinja2 templates with AST-based markdown processing."""

    def __init__(self, templates_dir: Path) -> None:
        """Initialize the renderer with templates directory."""
        logger.debug(
            f"Initializing CVRenderer with templates directory: {templates_dir}"
        )

        if not templates_dir.exists():
            logger.error(f"Templates directory does not exist: {templates_dir}")
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

        self.templates_dir = templates_dir

        self._filters = self._build_filters()

        self._globals = self._build_globals()

        self._env = self._build_env()

        # Initialize AST renderers
        self._ast_latex_renderer = ASTToLaTeXRenderer()
        self._ast_html_renderer = ASTToHTMLRenderer()
        self._ast_plain_renderer = ASTToPlainRenderer()

        logger.debug("CVRenderer initialization completed successfully")

    def _build_filters(self) -> Dict[str, Any]:
        filters: Dict[str, Callable[[Any], Any]] = {
            "escape_latex": escape_latex_text,
            "escape_html": escape_html_text,
            "markdown_latex": self._markdown_to_latex,
            "markdown_html": self._markdown_to_html,
            "markdown_plain": self._markdown_to_plain,
        }
        logger.debug(f"Built {len(filters)} Jinja2 filters: {list(filters.keys())}")
        return filters

    def _build_globals(self) -> Dict[str, Any]:
        globals: Dict[str, Any] = {
            "format_current_time": format_current_time,
            "normalize_url": normalize_url,
            "url_path": url_path,
            "dquoted": wrap_in_double_quotes,
            "str": str,
        }
        logger.debug(f"Built {len(globals)} Jinja2 globals: {list(globals.keys())}")
        return globals

    def _build_env(self) -> Environment:
        env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for filter_name, filter_func in self._filters.items():
            env.filters[filter_name] = filter_func

        for global_name, global_func in self._globals.items():
            env.globals[global_name] = global_func

        return env

    def load_raw_data(self, data_file: Path) -> Dict[str, Any]:
        """Load raw CV data from YAML file without validation."""
        logger.debug(f"Loading raw CV data from: {data_file}")

        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = yaml.safe_load(f)
                logger.debug(f"Successfully loaded YAML data: {data}")
                return data
        except FileNotFoundError:
            logger.error(f"CV data file not found: {data_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {data_file}: {e}")
            raise ValueError(f"Unable to parse {data_file} as YAML: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading {data_file}: {e}")
            raise

    def validate_cv_data(self, raw_data: Dict[str, Any]) -> CVData:
        """Validate CV data using Pydantic models."""
        logger.debug("Validating CV data using Pydantic models")

        try:
            # Validate using Pydantic model - it handles all conversion
            # automatically
            cv_data = CVData(**raw_data)
            logger.debug("CV data validation completed successfully")
            return cv_data
        except Exception as e:
            logger.error(f"CV data validation failed: {e}")
            raise ValueError(f"CV data validation failed: {e}")

    def load_data(self, data_file: Path) -> CVData:
        """Load and validate CV data from YAML file."""
        raw_data = self.load_raw_data(data_file)
        validated_data = self.validate_cv_data(raw_data)
        logger.debug("CV data loaded and validated successfully")
        return validated_data

    def _build_context(
        self, template_name: str, template_type: Optional[TemplateType]
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "template_name": template_name,
        }
        if template_type:
            context["template_type"] = template_type.value
        return context

    def _build_static(self, template_name: str) -> Dict[str, Any]:
        static: Dict[str, Any] = {
            "disclaimer_latex": self._render_disclaimer_latex(template_name),
            "disclaimer_html": self._render_disclaimer_html(template_name),
        }
        return static

    def _build_type_specific(
        self, data: Dict[str, Any], template_type: TemplateType
    ) -> Dict[str, Any]:
        type_specific = {}
        suffix = f"_{template_type.value}"
        for key, value in data.items():
            if key.endswith(suffix):
                short_key = key[: -(len(suffix))]
                type_specific[short_key] = value
        return type_specific

    def _build_inject(
        self, template_name: str, template_type: Optional[TemplateType]
    ) -> Dict[str, Any]:
        inject = {}

        inject["context"] = self._build_context(template_name, template_type)

        static_data = self._build_static(template_name)
        if template_type:
            type_specific_static = self._build_type_specific(static_data, template_type)
            if type_specific_static:
                logger.debug(
                    "Updating static data with type specific data: "
                    f"{type_specific_static.keys()}"
                )
                static_data.update(type_specific_static)
            else:
                logger.debug("No type specific static data found")
        inject["static"] = static_data

        return inject

    def render(
        self, template_name: str, cv_data: CVData, template_type: Optional[TemplateType]
    ) -> str:
        """Render CV using specified template and data."""
        try:
            logger.debug(f"Loading template: {template_name}")
            template = self._env.get_template(template_name)

            logger.debug("Converting CV data to dict")
            data = cv_data.model_dump()

            logger.debug("Building inject data")
            inject_data = self._build_inject(template_name, template_type)

            render_data = {**data, **inject_data}
            logger.debug(f"Render data: {render_data}")

            result: str = template.render(render_data)

            logger.debug(
                f"Template {template_name} rendered successfully "
                f"({len(result)} characters)"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def _generate_disclaimer(self, template_name: str) -> str:
        """Generate disclaimer comment based on template format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        disclaimer_lines = [
            "This file was automatically generated from a template.",
            "DO NOT EDIT THIS FILE DIRECTLY - your changes will be lost!",
            f"Generated on: {timestamp}",
            f"Template: {template_name}",
            "Generator: cv_renderer",
        ]

        return "\n".join(disclaimer_lines)

    def _render_disclaimer_latex(self, template_name: str) -> str:
        return self._ast_latex_renderer.render_comment(
            self._generate_disclaimer(template_name)
        )

    def _render_disclaimer_html(self, template_name: str) -> str:
        return self._ast_html_renderer.render_comment(
            self._generate_disclaimer(template_name)
        )

    def _process_markdown(self, markdown_text: Dict[str, Any], process: Any) -> str:
        logger.debug("Processing markdown text through AST renderer")
        if "ast" not in markdown_text:
            logger.error("Markdown text missing required 'ast' field")
            raise ValueError("Markdown text must contain an 'ast' field")

        ast_data = markdown_text["ast"]
        logger.debug(f"Processing AST with {len(ast_data)} tokens")
        result: str = process(ast_data)
        logger.debug(f"Markdown processing completed ({len(result)} characters)")
        return result

    def _markdown_to_latex(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to LaTeX."""
        logger.debug("Converting markdown to LaTeX format")
        return self._process_markdown(markdown_text, self._ast_to_latex)

    def _markdown_to_html(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to HTML."""
        logger.debug("Converting markdown to HTML format")
        return self._process_markdown(markdown_text, self._ast_to_html)

    def _markdown_to_plain(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to plain text."""
        logger.debug("Converting markdown to plain text format")
        return self._process_markdown(markdown_text, self._ast_to_plain)

    def _ast_to_latex(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to LaTeX."""
        logger.debug(f"Converting AST to LaTeX ({len(ast)} tokens)")
        result = self._ast_latex_renderer.render_ast(ast)
        logger.debug(f"AST to LaTeX conversion completed ({len(result)} characters)")
        return result

    def _ast_to_html(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to HTML."""
        logger.debug(f"Converting AST to HTML ({len(ast)} tokens)")
        result = self._ast_html_renderer.render_ast(ast)
        logger.debug(f"AST to HTML conversion completed ({len(result)} characters)")
        return result

    def _ast_to_plain(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to plain text."""
        logger.debug(f"Converting AST to plain text ({len(ast)} tokens)")
        result = self._ast_plain_renderer.render_ast(ast)
        logger.debug(
            f"AST to plain text conversion completed ({len(result)} characters)"
        )
        return result
