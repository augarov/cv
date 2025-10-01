#!/usr/bin/env python3
"""
CV Renderer CLI - Command-line interface for the CV renderer package.

Usage:
    python -m cv_renderer [--output OUTPUT] [--data DATA] [--template TEMPLATE]

Examples:
    python -m cv_renderer --data cv_data.yaml --template templates/cv.html.j2
    python -m cv_renderer --output cv.tex \
                          --data cv_data.yaml \
                          --template templates/cv.tex.j2
"""

import argparse
from pathlib import Path

from .renderer import CVRenderer


def make_output_file_name(template_path: Path) -> str:
    """Make output file name from template path."""
    if template_path.name.endswith(".j2"):
        return template_path.name[:-3]
    else:
        return template_path.name


def main() -> int:
    """Provide main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Render CV from YAML data using Jinja2 templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --output cv.tex
  %(prog)s --output cv.html --data custom_data.yaml
        """,
    )

    parser.add_argument(
        "--data",
        "-d",
        required=True,
        help="YAML data file path",
    )

    parser.add_argument(
        "--template",
        "-t",
        required=True,
        help="Template file path",
    )

    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output path",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing output file",
    )

    args = parser.parse_args()

    data_path = Path(args.data)
    template_path = Path(args.template)

    # Check if data file exists
    if not data_path.exists() or not data_path.is_file():
        print(f"❌ Error: Data file '{args.data}' not found")
        return 1

    # Check if template exists
    if not template_path.exists() or not template_path.is_file():
        print(f"❌ Error: Template file '{args.template}' not found")
        return 1

    if args.output is None:
        output_path = Path.cwd()
    else:
        output_path = Path(args.output)

    if output_path.is_dir():
        output_file = output_path / make_output_file_name(template_path)
    else:
        output_file = output_path
    print(f"📄 Output file will be saved to: {output_file}")

    parent_path = output_file.parent
    parent_path.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        if args.force:
            print(f"⚠️ Warning: Output file will be overwritten: {output_file}")
        else:
            print(
                f"❌ Error: Output file already exists: {output_file}."
                "Use --force to overwrite."
            )
            return 1

    output_file = output_file.resolve()
    data_path = data_path.resolve()
    template_path = template_path.resolve()

    paths = {data_path.as_posix(), template_path.as_posix(), output_file.as_posix()}
    if len(paths) != 3:
        err = "❌ Error: Paths are not unique:"
        for path in paths:
            err += f"\n  {path}"
        print(err)
        return 1

    try:

        templates_dir = template_path.parent
        template_name = template_path.name

        # Initialize renderer
        renderer = CVRenderer(templates_dir=templates_dir)

        # Load and validate data (always)
        print(f"🚀 Loading data from: {args.data}")
        print("🔍 Validating CV data using Pydantic models...")
        validated_data = renderer.load_data(data_path.as_posix())
        print("✅ Data validation successful!")
        data = renderer.convert_validated_data_for_templates(validated_data)

        # Render CV
        print(f"🔄 Rendering CV using template: {template_name}")
        renderer.render_to_file(template_name, data, output_file)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
