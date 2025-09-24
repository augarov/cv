"""
Core CV rendering functionality using Jinja2 templates with AST-based
markdown processing.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from enum import Enum

from .models import CVData
from .ast import (
    ASTToLaTeXRenderer,
    ASTToHTMLRenderer,
    ASTToPlainRenderer,
    escape_latex_text,
    escape_html_text
)


class TemplateFormat(Enum):
    """Supported template formats based on template file extensions."""
    LATEX = "latex"
    HTML = "html"


def detect_template_format(template_name: str) -> TemplateFormat:
    """Detect template format from template file extension.

    Args:
        template_name: Name of the template file (e.g., 'cv.tex.j2',
                       'cv.html.j2')

    Returns:
        TemplateFormat enum value

    Raises:
        ValueError: If template format is not supported (neither LaTeX
                    nor HTML)
    """
    template_path = Path(template_name)

    # Check for compound extensions like .tex.j2, .html.j2
    if template_path.suffixes:
        # Get the second-to-last suffix (e.g., .tex from .tex.j2)
        if len(template_path.suffixes) >= 2:
            format_extension = template_path.suffixes[-2].lower()
        else:
            format_extension = template_path.suffixes[-1].lower()

        if format_extension in ['.tex', '.latex']:
            return TemplateFormat.LATEX
        elif format_extension in ['.html', '.htm']:
            return TemplateFormat.HTML

    raise ValueError(
        f"Unsupported template format for '{template_name}'. "
        f"Only LaTeX (.tex.j2) and HTML (.html.j2) templates are supported."
    )


class CVRenderer:
    """CV Renderer using Jinja2 templates with AST-based markdown
    processing."""

    def __init__(self, templates_dir: str = "templates"):
        """Initialize the renderer with templates directory."""
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Initialize AST renderers
        self.ast_latex_renderer = ASTToLaTeXRenderer()
        self.ast_html_renderer = ASTToHTMLRenderer()
        self.ast_plain_renderer = ASTToPlainRenderer()

        # Add custom filters
        self.env.filters['escape_latex'] = escape_latex_text
        self.env.filters['escape_html'] = escape_html_text
        self.env.filters['markdown_latex'] = self._markdown_to_latex
        self.env.filters['markdown_html'] = self._markdown_to_html
        self.env.filters['markdown_plain'] = self._markdown_to_plain

    def load_raw_data(self, data_file: str) -> Dict[str, Any]:
        """Load raw CV data from YAML file without validation."""
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Unable to parse {data_file} as YAML: {e}")

    def validate_cv_data(self, raw_data: Dict[str, Any]) -> CVData:
        """Validate CV data using Pydantic models."""
        try:
            # Validate using Pydantic model - it handles all conversion
            # automatically
            return CVData(**raw_data)
        except Exception as e:
            raise ValueError(f"CV data validation failed: {e}")

    def load_data(self, data_file: str) -> CVData:
        """Load and validate CV data from YAML file."""
        raw_data = self.load_raw_data(data_file)
        return self.validate_cv_data(raw_data)

    def convert_validated_data_for_templates(
            self, cv_data: CVData) -> Dict[str, Any]:
        """Convert validated CVData to template-friendly format."""
        return cv_data.model_dump()

    def render(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render CV using specified template and data."""
        template = self.env.get_template(template_name)
        return template.render(**data)

    def render_to_file(self, template_name: str, data: Dict[str, Any],
                       output_file: str):
        """Render CV and save to file with disclaimer comment."""
        rendered = self.render(template_name, data)

        # Detect template format and generate disclaimer
        template_format = detect_template_format(template_name)
        disclaimer = self._generate_disclaimer(
            template_format, template_name
        )
        final_content = disclaimer + rendered

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        print(f"CV rendered to: {output_path}")

    def _generate_disclaimer(self, template_format: TemplateFormat,
                             template_name: str) -> str:
        """Generate disclaimer comment based on template format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        disclaimer_lines = [
            "This file was automatically generated from a template.",
            "DO NOT EDIT THIS FILE DIRECTLY - your changes will be lost!",
            f"Generated on: {timestamp}",
            f"Template: {template_name}",
            "Generator: cv_renderer"
        ]

        # Choose comment style based on template format
        match template_format:
            case TemplateFormat.LATEX:
                # LaTeX comment style
                comment_prefix = "% "
                disclaimer = "\n".join(
                    [comment_prefix + line for line in disclaimer_lines]
                )
                disclaimer += "\n" + "%" * 60 + "\n\n"
            case TemplateFormat.HTML:
                # HTML comment style
                disclaimer = "<!--\n"
                disclaimer += "\n".join(
                    ["  " + line for line in disclaimer_lines]
                )
                disclaimer += "\n-->\n\n"

        return disclaimer

    def _process_markdown(self, markdown_text: Dict[str, Any], process) -> str:
        if "ast" not in markdown_text:
            raise ValueError("Markdown text must contain an 'ast' field")
        res = process(markdown_text['ast'])
        return res

    def _markdown_to_latex(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to LaTeX."""
        return self._process_markdown(
            markdown_text, self._ast_to_latex
        )

    def _markdown_to_html(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to HTML."""
        return self._process_markdown(
            markdown_text, self._ast_to_html
        )

    def _ast_to_latex(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to LaTeX."""
        return self.ast_latex_renderer.render_ast(ast)

    def _ast_to_html(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to HTML."""
        return self.ast_html_renderer.render_ast(ast)

    def _markdown_to_plain(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to plain text."""
        return self._process_markdown(
            markdown_text, self._ast_to_plain
        )

    def _ast_to_plain(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to plain text."""
        return self.ast_plain_renderer.render_ast(ast)
