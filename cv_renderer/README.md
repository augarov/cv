# CV Renderer

Generate CV/Resume from YAML data using Jinja2 templates.

## Quick Start

```bash
poetry install
poetry run python -m cv_renderer
```

## Usage

```bash
poetry run python -m cv_renderer --data DATA [--input INPUT [INPUT ...]] [--output OUTPUT] [--force] [--log-level {DEBUG,INFO,WARNING,ERROR}] [--silent]
```

```bash
poetry run python -m cv_renderer --data cv_data.yaml --input templates/cv.html.j2
poetry run python -m cv_renderer -d cv_data.yaml -i templates/cv.tex.j2 -o cv.tex
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
  - category: Programming
    skills:
      - Python

experience:
  - company: "Company Name"
    position: "Your Position"
    achievements: ["Achievement 1", "Achievement 2"]
```

### Run Tests

```bash
poetry run pytest
```
