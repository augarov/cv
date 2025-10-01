# CV Renderer

Generate CV/Resume from YAML data using Jinja2 templates.

## Quick Start

```bash
cd cv_renderer
poetry install
poetry run python -m cv_renderer
```

## Usage

```bash
python -m cv_renderer [--output OUTPUT] [--data DATA] [--template TEMPLATE]
```

```bash
python -m cv_renderer --data cv_data.yaml --template templates/cv.html.j2
python -m cv_renderer --output cv.tex --data cv_data.yaml --template templates/cv.tex.j2
```

## Data Format

Edit `cv_data.yaml` with your information:

```yaml
personal:
  name: { first: "Your", last: "Name" }
  title: "Your Title"
  contact:
    email: your.email@example.com

skills:
  Programming: ["Skill 1", "Skill 2"]

experience:
  - company: "Company Name"
    position: "Your Position"
    achievements: ["Achievement 1", "Achievement 2"]
```
