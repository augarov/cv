"""
Core CV rendering functionality using Jinja2 templates with AST-based markdown processing.
"""

import yaml
import mistune
from pathlib import Path
from typing import Dict, Any, Union, List, cast
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

from .models import CVData, MarkdownText

class TemplateFormat(Enum):
    """Supported template formats based on template file extensions."""
    LATEX = "latex"
    HTML = "html"


def detect_template_format(template_name: str) -> TemplateFormat:
    """Detect template format from template file extension.

    Args:
        template_name: Name of the template file (e.g., 'cv.tex.j2', 'cv.html.j2')

    Returns:
        TemplateFormat enum value

    Raises:
        ValueError: If template format is not supported (neither LaTeX nor HTML)
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

    raise ValueError(f"Unsupported template format for '{template_name}'. "
                     f"Only LaTeX (.tex.j2) and HTML (.html.j2) templates are supported.")


def escape_latex_text(text: str) -> str:
    """Escape special LaTeX characters and handle newlines in plain text."""
    if not isinstance(text, str):
        return text

    # Process backslashes first to avoid double-escaping
    text = text.replace('\\', r'\textbackslash{}')

    # Then process other special characters
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
    }

    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)

    # Handle newlines for LaTeX
    # Handle double newlines as paragraph breaks
    text = text.replace('\n\n', '\n\n\\par\n')
    # Handle single newlines as line breaks
    text = text.replace('\n', ' \\\\\n')

    return text


def escape_html_text(text: str) -> str:
    """Escape special HTML characters and handle newlines in plain text."""
    if not isinstance(text, str):
        return text

    # Escape special HTML characters
    html_special_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
    }

    for char, replacement in html_special_chars.items():
        text = text.replace(char, replacement)

    # Handle newlines for HTML
    # Handle double newlines as paragraph breaks
    text = text.replace('\n\n', '</p><p>')
    # Handle single newlines as line breaks
    text = text.replace('\n', '<br>')

    # Wrap the entire text in paragraph tags if it contains paragraph breaks
    if '</p><p>' in text:
        text = f'<p>{text}</p>'

    return text


class ASTRenderer(ABC):
    """Base class for AST renderers."""

    def render_ast(self, ast: List[Dict[str, Any]]) -> str:
        """Render AST tokens to output format."""
        return ''.join(self._render_token(token) for token in ast)

    def _render_token(self, token: Dict[str, Any]) -> str:
        """Render a single AST token to output format."""
        token_type = token.get('type', '')

        match token_type:
            case 'paragraph':
                children_text = self._render_children(token)
                return self._render_paragraph(children_text)

            case 'text':
                return self._render_text(token.get('raw', ''))

            case 'strong':
                children_text = self._render_children(token)
                return self._render_strong(children_text)

            case 'linebreak':
                return self._render_linebreak()

            case 'softbreak':
                return self._render_softbreak()

            case _:
                # Handle unknown token types by rendering children if they exist
                return self._render_children(token)

    def _render_children(self, token: Dict[str, Any]) -> str:
        """Render children of a token."""
        children = token.get('children', [])
        return ''.join(self._render_token(child) for child in children)

    # Abstract methods that subclasses must implement
    @abstractmethod
    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph."""
        pass

    @abstractmethod
    def _render_text(self, text: str) -> str:
        """Render plain text."""
        pass

    @abstractmethod
    def _render_strong(self, children_text: str) -> str:
        """Render bold text."""
        pass

    @abstractmethod
    def _render_linebreak(self) -> str:
        """Render a line break."""
        pass

    @abstractmethod
    def _render_softbreak(self) -> str:
        """Render a soft break."""
        pass


class ASTToLaTeXRenderer(ASTRenderer):
    """Renderer for converting AST to LaTeX."""

    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph for LaTeX."""
        return f"{children_text}\n\n"

    def _render_text(self, text: str) -> str:
        """Render plain text for LaTeX."""
        return escape_latex_text(text)

    def _render_strong(self, children_text: str) -> str:
        """Render bold text for LaTeX."""
        return f"\\textbf{{{children_text}}}"

    def _render_linebreak(self) -> str:
        """Render a line break for LaTeX."""
        return ' \\\\\n'

    def _render_softbreak(self) -> str:
        """Render a soft break for LaTeX."""
        return ' '


class ASTToHTMLRenderer(ASTRenderer):
    """Renderer for converting AST to HTML."""

    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph for HTML."""
        return f"<p>{children_text}</p>\n"

    def _render_text(self, text: str) -> str:
        """Render plain text for HTML."""
        return escape_html_text(text)

    def _render_strong(self, children_text: str) -> str:
        """Render bold text for HTML."""
        return f"<strong>{children_text}</strong>"

    def _render_linebreak(self) -> str:
        """Render a line break for HTML."""
        return '<br>\n'

    def _render_softbreak(self) -> str:
        """Render a soft break for HTML."""
        return ' '


class CVRenderer:
    """CV Renderer using Jinja2 templates with AST-based markdown processing."""

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

        # Add custom filters
        self.env.filters['escape_latex'] = escape_latex_text
        self.env.filters['escape_html'] = escape_html_text
        self.env.filters['markdown_latex'] = self._markdown_to_latex
        self.env.filters['markdown_html'] = self._markdown_to_html

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
            # Validate using Pydantic model - it handles all conversion automatically
            return CVData(**raw_data)
        except Exception as e:
            raise ValueError(f"CV data validation failed: {e}")

    def load_data(self, data_file: str) -> CVData:
        """Load and validate CV data from YAML file."""
        raw_data = self.load_raw_data(data_file)
        return self.validate_cv_data(raw_data)

    def convert_validated_data_for_templates(self, cv_data: CVData) -> Dict[str, Any]:
        """Convert validated CVData to template-friendly format."""
        return cv_data.model_dump()

    def render(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render CV using specified template and data."""
        template = self.env.get_template(template_name)
        return template.render(**data)

    def render_to_file(self, template_name: str, data: Dict[str, Any], output_file: str):
        """Render CV and save to file with disclaimer comment."""
        rendered = self.render(template_name, data)

        # Detect template format and generate disclaimer
        template_format = detect_template_format(template_name)
        disclaimer = self._generate_disclaimer(template_format, template_name)
        final_content = disclaimer + rendered

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        print(f"✅ CV rendered to: {output_path}")

    def _generate_disclaimer(self, template_format: TemplateFormat, template_name: str) -> str:
        """Generate disclaimer comment based on template format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        disclaimer_lines = [
            "This file was automatically generated from a template.",
            "DO NOT EDIT THIS FILE DIRECTLY - your changes will be lost!",
            f"Generated on: {timestamp}",
            f"Template: {template_name}",
            f"Generator: cv_renderer"
        ]

        # Choose comment style based on template format
        match template_format:
            case TemplateFormat.LATEX:
                # LaTeX comment style
                comment_prefix = "% "
                disclaimer = "\n".join([comment_prefix + line for line in disclaimer_lines])
                disclaimer += "\n" + "%" * 60 + "\n\n"
            case TemplateFormat.HTML:
                # HTML comment style
                disclaimer = "<!--\n"
                disclaimer += "\n".join(["  " + line for line in disclaimer_lines])
                disclaimer += "\n-->\n\n"

        return disclaimer

    def _process_markdown(self, markdown_text: Dict[str, Any], process) -> str:
        if "ast" not in markdown_text:
            raise ValueError("Markdown text must contain an 'ast' field")
        return process(markdown_text['ast'])

    def _markdown_to_latex(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to LaTeX."""
        return self._process_markdown(markdown_text, self._ast_to_latex)

    def _markdown_to_html(self, markdown_text: Dict[str, Any]) -> str:
        """Convert markdown text to HTML."""
        return self._process_markdown(markdown_text, self._ast_to_html)

    def _ast_to_latex(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to LaTeX."""
        return self.ast_latex_renderer.render_ast(ast)

    def _ast_to_html(self, ast: List[Dict[str, Any]]) -> str:
        """Convert AST to HTML."""
        return self.ast_html_renderer.render_ast(ast)