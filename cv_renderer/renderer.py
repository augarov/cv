"""
Core CV rendering functionality using Jinja2 templates.
"""

import yaml
import mistune
from pathlib import Path
from typing import Dict, Any, Union
from jinja2 import Environment, FileSystemLoader, select_autoescape


class LaTeXRenderer(mistune.HTMLRenderer):
    """Custom renderer for converting markdown to LaTeX."""

    def strong(self, text: str) -> str:
        """Render bold text for LaTeX."""
        return f"\\textbf{{{text}}}"

    def paragraph(self, text: str) -> str:
        """Render paragraph for LaTeX (no special wrapper needed)."""
        return text

    def text(self, text: str) -> str:
        """Render plain text with LaTeX escaping."""
        return self._escape_latex_text(text)

    def _escape_latex_text(self, text: str) -> str:
        """Escape special LaTeX characters in plain text."""
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

        return text


class HTMLRenderer(mistune.HTMLRenderer):
    """Custom renderer for converting markdown to HTML."""

    def strong(self, text: str) -> str:
        """Render bold text for HTML."""
        return f"<strong>{text}</strong>"


class CVRenderer:
    """CV Renderer using Jinja2 templates."""

    def __init__(self, templates_dir: str = "templates"):
        """Initialize the renderer with templates directory."""
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Initialize markdown parsers
        self.latex_markdown = mistune.create_markdown(renderer=LaTeXRenderer())
        self.html_markdown = mistune.create_markdown(renderer=HTMLRenderer())

        # Add custom filters
        self.env.filters['escape_latex'] = self._escape_latex
        self.env.filters['format_skills'] = self._format_skills
        self.env.filters['markdown_latex'] = self._markdown_to_latex
        self.env.filters['markdown_html'] = self._markdown_to_html
        self.env.filters['markdown'] = self._markdown_auto

    def load_data(self, data_file: str) -> Dict[str, Any]:
        """Load CV data from YAML file."""
        with open(data_file, 'r', encoding='utf-8') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Unable to parse {data_file} as YAML: {e}")

    def render(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render CV using specified template and data."""
        template = self.env.get_template(template_name)
        return template.render(**data)

    def render_to_file(self, template_name: str, data: Dict[str, Any], output_file: str):
        """Render CV and save to file."""
        rendered = self.render(template_name, data)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)

        print(f"✅ CV rendered to: {output_path}")

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
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

        return text

    def _format_skills(self, skills: Dict[str, list]) -> Dict[str, list]:
        """Format skills for LaTeX rendering."""
        # This filter can be customized based on output format
        return skills

    def _markdown_to_latex(self, text: str) -> str:
        """Convert markdown text to LaTeX."""
        if not isinstance(text, str):
            return str(text)
        return self.latex_markdown(text).strip()

    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown text to HTML."""
        if not isinstance(text, str):
            return str(text)
        return self.html_markdown(text).strip()

    def _markdown_auto(self, text: str) -> str:
        """Auto-detect output format and convert markdown accordingly."""
        if not isinstance(text, str):
            return str(text)

        # Check if we're in a template context to determine output format
        # For now, default to LaTeX (can be enhanced with context detection)
        return self._markdown_to_latex(text)