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
# Generate LaTeX (default)
poetry run python -m cv_renderer

# Generate HTML
poetry run python -m cv_renderer --format html --output cv.html

# Custom data file
poetry run python -m cv_renderer --data custom_data.yaml
```

## Data Format

Edit `cv_data.yaml` with your information:

```yaml
personal:
  name: {first: "Your", last: "Name"}
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
