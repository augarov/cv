# CV Renderer

Render a [rendercv](https://docs.rendercv.com/) CV to Typst, PDF and website files. rendercv validates the YAML and renders the Typst source; the website templates are rendered with our own Jinja2 environment from the same model.

In this repo, run it through `make` (see the top-level `README.md`). The commands below are for running it by hand from `cv_renderer/` inside the project venv (`make install-deps-python`, then `. ../.venv/bin/activate`).

## Usage

```bash
python -m cv_renderer [--log-level {DEBUG,INFO,WARNING,ERROR}] [--silent] SUBCOMMAND ...
```

| Subcommand | Reads                                                         | Writes                                               |
| ---------- | ------------------------------------------------------------- | ---------------------------------------------------- |
| `typst`    | `--cv` and optionally `--design`, `--locale`, `--settings`    | `--output`: the Typst source (theme from the design) |
| `pdf`      | `--input`: a `.typ` file                                      | `--output`: the PDF                                  |
| `web`      | the same inputs as `typst`, plus `--website` and `--template` | `--output`: the rendered template                    |

```bash
python -m cv_renderer typst --cv ../cv/cv.yaml --design ../cv/design.yaml --output ../build/pdf/cv.typ
python -m cv_renderer pdf --input ../build/pdf/cv.typ --output ../build/pdf/cv.pdf
python -m cv_renderer web --cv ../cv/cv.yaml --website ../cv/website.yaml \
    --template ../templates/web/index.html.j2 --output ../build/web/index.html
```

The build date is `settings.current_date` if that is an explicit date, otherwise `SOURCE_DATE_EPOCH`, otherwise today. Errors are printed as one line naming the file and exit with status 1.

## Run tests

```bash
pytest
```
