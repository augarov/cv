"""
Core CV rendering functionality using Jinja2 templates.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape


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

        # Add custom filters
        self.env.filters['escape_latex'] = self._escape_latex
        self.env.filters['format_skills'] = self._format_skills

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