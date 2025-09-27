#!/usr/bin/env python3
"""
CV Renderer CLI - Command-line interface for the CV renderer package.

Usage:
    python -m cv_renderer [--format FORMAT] [--output OUTPUT] [--data DATA]

Examples:
    python -m cv_renderer --format latex --output tex/cv.tex
    python -m cv_renderer --format html --output cv.html
"""

import argparse
from pathlib import Path

from .renderer import CVRenderer


def main() -> int:
    """Provide main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Render CV from YAML data using Jinja2 templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --format latex --output tex/cv.tex
  %(prog)s --format html --output cv.html --data custom_data.yaml
        """,
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["latex", "html"],
        default="latex",
        help="Output format (default: latex)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="tex/cv.tex",
        help="Output file path (default: tex/cv.tex)",
    )

    parser.add_argument(
        "--data",
        "-d",
        default="cv_data.yaml",
        help="YAML data file path (default: cv_data.yaml)",
    )

    parser.add_argument(
        "--templates-dir",
        "-t",
        default="templates",
        help="Templates directory (default: templates)",
    )

    args = parser.parse_args()

    # Check if data file exists
    if not Path(args.data).exists():
        print(f"❌ Error: Data file '{args.data}' not found")
        return 1

    # Template file mapping
    template_files = {"latex": "cv.tex.j2", "html": "cv.html.j2"}

    template_file = template_files.get(args.format)
    if not template_file:
        print(f"❌ Error: Unsupported format '{args.format}'")
        return 1

    # Check if template exists
    template_path = Path(args.templates_dir) / template_file
    if not template_path.exists():
        print(f"❌ Error: Template file '{template_path}' not found")
        print("💡 Please create the template file or check the templates directory")
        return 1

    try:
        # Initialize renderer
        renderer = CVRenderer(templates_dir=args.templates_dir)

        # Load and validate data (always)
        print(f"📄 Loading data from: {args.data}")
        print("🔍 Validating CV data using Pydantic models...")
        validated_data = renderer.load_data(args.data)
        print("✅ Data validation successful!")
        data = renderer.convert_validated_data_for_templates(validated_data)

        # Render CV
        print(f"🔄 Rendering CV using template: {template_file}")
        renderer.render_to_file(template_file, data, args.output)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
